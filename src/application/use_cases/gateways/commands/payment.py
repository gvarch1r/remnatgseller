import time
import uuid
from dataclasses import dataclass, replace
from uuid import UUID

from loguru import logger

from src.application.common import (
    EventPublisher,
    Interactor,
    Notifier,
    TranslatorHub,
    TranslatorRunner,
)
from src.application.common.dao import (
    PaymentGatewayDao,
    ReferralDao,
    SubscriptionDao,
    TransactionDao,
    UserDao,
)
from src.application.common.policy import Permission
from src.application.common.uow import UnitOfWork
from src.application.dto import (
    PaymentResultDto,
    PlanSnapshotDto,
    PriceDetailsDto,
    TransactionDto,
    UserDto,
)
from src.application.dto.payment_gateway import (
    CryptomusGatewaySettingsDto,
    CryptopayGatewaySettingsDto,
    FreeKassaGatewaySettingsDto,
    HeleketGatewaySettingsDto,
    MulenPayGatewaySettingsDto,
    PayMasterGatewaySettingsDto,
    PaymentGatewayDto,
    PlategaGatewaySettingsDto,
    RobokassaGatewaySettingsDto,
    UrlPayGatewaySettingsDto,
    WataGatewaySettingsDto,
    YookassaGatewaySettingsDto,
    YoomoneyGatewaySettingsDto,
)
from src.application.events import UserPurchaseEvent
from src.application.use_cases.gateways.queries.providers import GetPaymentGatewayInstance
from src.application.use_cases.referral.commands.rewards import (
    AssignReferralRewards,
    AssignReferralRewardsDto,
)
from src.application.use_cases.subscription.commands.purchase import (
    PurchaseSubscription,
    PurchaseSubscriptionDto,
)
from src.core.enums import (
    Currency,
    PaymentGatewayType,
    PurchaseType,
    TransactionStatus,
    ensure_currency,
    ensure_payment_gateway_type,
    ensure_purchase_type,
)
from src.core.utils.i18n_helpers import (
    i18n_format_days,
    i18n_format_device_limit,
    i18n_format_traffic_limit,
)


class CreateDefaultPaymentGateway(Interactor[None, None]):
    required_permission = None

    def __init__(self, uow: UnitOfWork, gateway_dao: PaymentGatewayDao) -> None:
        self.uow = uow
        self.gateway_dao = gateway_dao

    async def _execute(self, actor: UserDto, data: None) -> None:
        async with self.uow:
            for gateway_type in PaymentGatewayType:
                if await self.gateway_dao.get_by_type(gateway_type):
                    continue

                is_active = gateway_type == PaymentGatewayType.TELEGRAM_STARS

                settings_map = {
                    PaymentGatewayType.YOOKASSA: YookassaGatewaySettingsDto,
                    PaymentGatewayType.YOOMONEY: YoomoneyGatewaySettingsDto,
                    PaymentGatewayType.CRYPTOMUS: CryptomusGatewaySettingsDto,
                    PaymentGatewayType.HELEKET: HeleketGatewaySettingsDto,
                    PaymentGatewayType.CRYPTOPAY: CryptopayGatewaySettingsDto,
                    PaymentGatewayType.FREEKASSA: FreeKassaGatewaySettingsDto,
                    PaymentGatewayType.MULENPAY: MulenPayGatewaySettingsDto,
                    PaymentGatewayType.PAYMASTER: PayMasterGatewaySettingsDto,
                    PaymentGatewayType.PLATEGA: PlategaGatewaySettingsDto,
                    PaymentGatewayType.ROBOKASSA: RobokassaGatewaySettingsDto,
                    PaymentGatewayType.URLPAY: UrlPayGatewaySettingsDto,
                    PaymentGatewayType.WATA: WataGatewaySettingsDto,
                }
                dto_class = settings_map.get(gateway_type)
                settings = dto_class() if dto_class else None

                await self.gateway_dao.create(
                    PaymentGatewayDto(
                        type=gateway_type,
                        currency=Currency.from_gateway_type(gateway_type),
                        is_active=is_active,
                        settings=settings,
                    )
                )
                logger.info(f"Payment gateway '{gateway_type}' created")

            await self.uow.commit()


@dataclass(frozen=True)
class CreatePaymentDto:
    plan_snapshot: PlanSnapshotDto
    pricing: PriceDetailsDto
    purchase_type: PurchaseType
    gateway_type: PaymentGatewayType


class CreatePayment(Interactor[CreatePaymentDto, PaymentResultDto]):
    required_permission = Permission.PUBLIC

    def __init__(
        self,
        uow: UnitOfWork,
        payment_gateway_dao: PaymentGatewayDao,
        transaction_dao: TransactionDao,
        get_payment_gateway_instance: GetPaymentGatewayInstance,
        translator_hub: TranslatorHub,
    ) -> None:
        self.uow = uow
        self.payment_gateway_dao = payment_gateway_dao
        self.transaction_dao = transaction_dao
        self.get_payment_gateway_instance = get_payment_gateway_instance
        self.translator_hub = translator_hub

    async def _execute(self, actor: UserDto, data: CreatePaymentDto) -> PaymentResultDto:
        gateway_type = ensure_payment_gateway_type(data.gateway_type)
        purchase_type = ensure_purchase_type(data.purchase_type)

        flow_id = str(uuid.uuid4())
        pay_log = logger.bind(
            payment_flow_id=flow_id,
            user_telegram_id=actor.telegram_id,
            gateway_type=gateway_type.value,
            purchase_type=purchase_type.value,
        )
        gateway_instance = await self.get_payment_gateway_instance.system(gateway_type)
        i18n = self.translator_hub.get_translator_by_locale(actor.language)

        if purchase_type == PurchaseType.ADD_DEVICES:
            details = i18n.get(
                "payment-invoice-add-devices",
                name=data.plan_snapshot.name,
                device_count=data.plan_snapshot.device_limit,
            )
        else:
            key, kw = i18n_format_days(data.plan_snapshot.duration)
            details = i18n.get(
                "payment-invoice-description",
                purchase_type=purchase_type,
                name=data.plan_snapshot.name,
                duration=i18n.get(key, **kw),
            )

        gw_currency = ensure_currency(gateway_instance.data.currency)
        gateway_instance.data = replace(gateway_instance.data, currency=gw_currency)

        transaction = TransactionDto(
            payment_id=uuid.uuid4(),
            user_telegram_id=actor.telegram_id,
            status=TransactionStatus.PENDING,
            purchase_type=purchase_type,
            gateway_type=gateway_instance.data.type,
            pricing=data.pricing,
            currency=gw_currency,
            plan_snapshot=data.plan_snapshot,
        )

        async with self.uow:
            if data.pricing.is_free:
                await self.transaction_dao.create(transaction)
                await self.uow.commit()

                pay_log.info("create_payment free transaction only (no provider call)")
                return PaymentResultDto(id=transaction.payment_id, url=None)

            t0 = time.perf_counter()
            try:
                payment = await gateway_instance.handle_create_payment(
                    amount=data.pricing.final_amount,
                    details=details,
                )
            except Exception:
                pay_log.exception("create_payment provider call failed")
                raise
            elapsed_ms = (time.perf_counter() - t0) * 1000

            transaction.payment_id = payment.id
            await self.transaction_dao.create(transaction)
            await self.uow.commit()

        pay_log.info(
            "create_payment success payment_id={} elapsed_ms={:.1f} currency={}",
            str(payment.id),
            elapsed_ms,
            gw_currency.value,
        )
        return payment


class CreateTestPayment(Interactor[PaymentGatewayType, PaymentResultDto]):
    required_permission = Permission.REMNASHOP_GATEWAYS

    def __init__(
        self,
        uow: UnitOfWork,
        payment_gateway_dao: PaymentGatewayDao,
        transaction_dao: TransactionDao,
        get_payment_gateway_instance: GetPaymentGatewayInstance,
        translator_hub: TranslatorHub,
    ) -> None:
        self.uow = uow
        self.payment_gateway_dao = payment_gateway_dao
        self.transaction_dao = transaction_dao
        self.get_payment_gateway_instance = get_payment_gateway_instance
        self.translator_hub = translator_hub

    async def _execute(self, actor: UserDto, gateway_type: PaymentGatewayType) -> PaymentResultDto:
        gateway_instance = await self.get_payment_gateway_instance.system(gateway_type)
        i18n = self.translator_hub.get_translator_by_locale(actor.language)

        test_pricing = PriceDetailsDto.test()
        test_plan_snapshot = PlanSnapshotDto.test()

        payment: PaymentResultDto = await gateway_instance.handle_create_payment(
            amount=test_pricing.final_amount,
            details=i18n.get("test-payment"),
        )

        async with self.uow:
            transaction = TransactionDto(
                payment_id=payment.id,
                user_telegram_id=actor.telegram_id,
                status=TransactionStatus.PENDING,
                is_test=True,
                purchase_type=PurchaseType.NEW,
                gateway_type=gateway_instance.data.type,
                pricing=test_pricing,
                currency=gateway_instance.data.currency,
                plan_snapshot=test_plan_snapshot,
            )
            await self.transaction_dao.create(transaction)
            await self.uow.commit()

        logger.info(f"Created test transaction '{payment.id}' for user '{actor.telegram_id}'")
        return payment


@dataclass(frozen=True)
class ProcessPaymentDto:
    payment_id: UUID
    new_transaction_status: TransactionStatus


class ProcessPayment(Interactor[ProcessPaymentDto, None]):
    required_permission = None

    def __init__(
        self,
        uow: UnitOfWork,
        user_dao: UserDao,
        transaction_dao: TransactionDao,
        subscription_dao: SubscriptionDao,
        referral_dao: ReferralDao,
        event_publisher: EventPublisher,
        notifier: Notifier,
        i18n: TranslatorRunner,
        assign_referral_rewards: AssignReferralRewards,
        purchase_subscription: PurchaseSubscription,
    ) -> None:
        self.uow = uow
        self.user_dao = user_dao
        self.transaction_dao = transaction_dao
        self.subscription_dao = subscription_dao
        self.referral_dao = referral_dao
        self.event_publisher = event_publisher
        self.notifier = notifier
        self.i18n = i18n
        self.assign_referral_rewards = assign_referral_rewards
        self.purchase_subscription = purchase_subscription

    async def _execute(self, actor: UserDto, data: ProcessPaymentDto) -> None:
        payment_id = data.payment_id
        new_status = data.new_transaction_status
        plog = logger.bind(
            payment_id=str(payment_id),
            payment_event=new_status.value,
        )

        async with self.uow:
            transaction = await self.transaction_dao.get_by_payment_id(payment_id)

            if not transaction:
                plog.critical("process_payment transaction not found")
                return

            user = await self.user_dao.get_by_telegram_id(transaction.user_telegram_id)

            if not user:
                plog.critical("process_payment user not found for transaction")
                return

            plog = plog.bind(user_telegram_id=user.telegram_id, gateway_type=transaction.gateway_type.value)

            if new_status == TransactionStatus.CANCELED:
                updated = await self.transaction_dao.try_transition_status(
                    payment_id,
                    TransactionStatus.PENDING,
                    TransactionStatus.CANCELED,
                )
                if not updated:
                    if transaction.is_completed:
                        plog.info("process_payment cancel webhook ignored (already completed)")
                    else:
                        plog.warning(
                            "process_payment cancel skipped (not pending)",
                            current_status=transaction.status.value,
                        )
                    return
                await self.uow.commit()
                plog.info("process_payment marked canceled")
                return

            if new_status == TransactionStatus.COMPLETED:
                updated = await self.transaction_dao.try_transition_status(
                    payment_id,
                    TransactionStatus.PENDING,
                    TransactionStatus.COMPLETED,
                )
                if not updated:
                    refreshed = await self.transaction_dao.get_by_payment_id(payment_id)
                    if refreshed and refreshed.is_completed:
                        plog.info("process_payment duplicate webhook ignored (already completed)")
                    else:
                        plog.warning(
                            "process_payment complete skipped (not pending)",
                            current_status=transaction.status.value,
                        )
                    return
                await self._handle_success(user, updated)
                await self.uow.commit()
                plog.info("process_payment completed and subscription applied")
                return

            plog.warning("process_payment unhandled status")

    async def _handle_success(self, user: UserDto, transaction: TransactionDto) -> None:
        if transaction.is_test:
            await self.notifier.notify_user(user, i18n_key="ntf-gateway.test-payment-confirmed")
            return

        subscription = await self.subscription_dao.get_current(user.telegram_id)
        old_plan = subscription.plan_snapshot if subscription else None

        event = UserPurchaseEvent(
            telegram_id=user.telegram_id,
            name=user.name,
            username=user.username,
            #
            purchase_type=transaction.purchase_type,
            is_trial_plan=transaction.plan_snapshot.is_trial,
            payment_id=transaction.payment_id,
            gateway_type=transaction.gateway_type,
            final_amount=transaction.pricing.final_amount,
            discount_percent=transaction.pricing.discount_percent,
            original_amount=transaction.pricing.original_amount,
            currency=transaction.currency.symbol,
            #
            plan_name=transaction.plan_snapshot.name,
            plan_type=transaction.plan_snapshot.type,
            plan_traffic_limit=i18n_format_traffic_limit(transaction.plan_snapshot.traffic_limit),
            plan_device_limit=i18n_format_device_limit(transaction.plan_snapshot.device_limit),
            plan_duration=i18n_format_days(transaction.plan_snapshot.duration),
            #
            previous_plan_name=self.i18n.get(old_plan.name) if old_plan else "N/A",
            previous_plan_type={
                "key": "plan-type",
                "plan_type": old_plan.type if old_plan else "N/A",
            },
            previous_plan_traffic_limit=i18n_format_traffic_limit(old_plan.traffic_limit)
            if old_plan
            else "N/A",
            previous_plan_device_limit=i18n_format_device_limit(old_plan.device_limit)
            if old_plan
            else "N/A",
            previous_plan_duration=i18n_format_days(old_plan.duration) if old_plan else "N/A",
        )

        await self.event_publisher.publish(event)
        await self.purchase_subscription.system(
            PurchaseSubscriptionDto(user, transaction, subscription)
        )

        if not transaction.pricing.is_free:
            await self.assign_referral_rewards.system(AssignReferralRewardsDto(user, transaction))
