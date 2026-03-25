import uuid
from typing import Optional, TypedDict, cast

from adaptix import Retort
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from loguru import logger
from redis.asyncio import Redis

from src.application.common import Notifier, TranslatorRunner
from src.application.common.dao import (
    DeviceAddonDao,
    PaymentGatewayDao,
    PlanDao,
    SettingsDao,
    SubscriptionDao,
)
from src.application.dto import (
    DeviceAddonDto,
    MessagePayloadDto,
    PlanDto,
    PlanSnapshotDto,
    SubscriptionDto,
    UserDto,
)
from src.application.services import PricingService
from src.application.use_cases.gateways.commands.payment import (
    CreatePayment,
    CreatePaymentDto,
    ProcessPayment,
    ProcessPaymentDto,
)
from src.application.use_cases.plan.queries.match import MatchPlan, MatchPlanDto
from src.application.use_cases.subscription.commands.promocode import ActivatePromocode, ActivatePromocodeDto
from src.application.use_cases.user.queries.plans import GetAvailablePlans
from src.core.constants import PAYMENT_PREFIX, USER_KEY
from src.core.enums import PaymentGatewayType, PurchaseType, TransactionStatus
from src.core.utils.rate_limit import is_rate_limited
from src.telegram.states import Subscription

PAYMENT_CACHE_KEY = "payment_cache"
CURRENT_DURATION_KEY = "selected_duration"
CURRENT_METHOD_KEY = "selected_payment_method"


def _trial_renew_blocked(
    current_subscription: Optional[SubscriptionDto],
    purchase_type: PurchaseType,
) -> bool:
    return purchase_type == PurchaseType.RENEW and (
        current_subscription is not None and current_subscription.is_trial
    )


class CachedPaymentData(TypedDict):
    payment_id: str
    payment_url: Optional[str]
    final_pricing: str


def _get_cache_key(duration: int, gateway_type: PaymentGatewayType) -> str:
    return f"{duration}:{gateway_type.value}"


def _get_addon_cache_key(device_count: int, gateway_type: PaymentGatewayType) -> str:
    return f"addon:{device_count}:{gateway_type.value}"


def _load_payment_data(dialog_manager: DialogManager) -> dict[str, CachedPaymentData]:
    if PAYMENT_CACHE_KEY not in dialog_manager.dialog_data:
        dialog_manager.dialog_data[PAYMENT_CACHE_KEY] = {}
    return cast(dict[str, CachedPaymentData], dialog_manager.dialog_data[PAYMENT_CACHE_KEY])


def _save_payment_data(dialog_manager: DialogManager, payment_data: CachedPaymentData) -> None:
    dialog_manager.dialog_data["payment_id"] = payment_data["payment_id"]
    dialog_manager.dialog_data["payment_url"] = payment_data["payment_url"]
    dialog_manager.dialog_data["final_pricing"] = payment_data["final_pricing"]


async def _create_payment_and_get_data(
    dialog_manager: DialogManager,
    plan: PlanDto,
    duration_days: int,
    gateway_type: PaymentGatewayType,
    retort: Retort,
    payment_gateway_dao: PaymentGatewayDao,
    notifier: Notifier,
    pricing_service: PricingService,
    create_payment: CreatePayment,
) -> Optional[CachedPaymentData]:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    duration = plan.get_duration(duration_days)
    payment_gateway = await payment_gateway_dao.get_by_type(gateway_type)
    purchase_type: PurchaseType = dialog_manager.dialog_data["purchase_type"]

    if not duration or not payment_gateway:
        logger.error(f"{user.log} Failed to find duration or gateway for payment creation")
        return None

    transaction_plan = PlanSnapshotDto.from_plan(plan, duration.days)
    price = duration.get_price(payment_gateway.currency)
    pricing = pricing_service.calculate(user, price, payment_gateway.currency)

    try:
        result = await create_payment(
            user,
            CreatePaymentDto(
                plan_snapshot=transaction_plan,
                pricing=pricing,
                purchase_type=purchase_type,
                gateway_type=gateway_type,
            ),
        )

        return CachedPaymentData(
            payment_id=str(result.id),
            payment_url=result.url,
            final_pricing=retort.dump(pricing),
        )

    except Exception as e:
        ref = uuid.uuid4().hex[:12]
        logger.exception(
            "{} payment_create_failed ref={} error={}",
            user.log,
            ref,
            e,
        )
        await notifier.notify_user(
            user,
            payload=MessagePayloadDto(
                i18n_key="ntf-subscription.payment-creation-failed",
                i18n_kwargs={"ref": ref},
            ),
        )
        raise


async def _create_payment_add_devices(
    dialog_manager: DialogManager,
    device_addon: DeviceAddonDto,
    gateway_type: PaymentGatewayType,
    retort: Retort,
    payment_gateway_dao: PaymentGatewayDao,
    notifier: Notifier,
    pricing_service: PricingService,
    create_payment: CreatePayment,
) -> Optional[CachedPaymentData]:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    payment_gateway = await payment_gateway_dao.get_by_type(gateway_type)
    price = device_addon.get_price(payment_gateway.currency) if payment_gateway else None

    if not price or not payment_gateway:
        logger.error(f"{user.log} No price or gateway for device addon payment")
        return None

    transaction_plan = PlanSnapshotDto.from_device_addon(device_addon.device_count)
    pricing = pricing_service.calculate(user, price, payment_gateway.currency)

    try:
        result = await create_payment(
            user,
            CreatePaymentDto(
                plan_snapshot=transaction_plan,
                pricing=pricing,
                purchase_type=PurchaseType.ADD_DEVICES,
                gateway_type=gateway_type,
            ),
        )

        return CachedPaymentData(
            payment_id=str(result.id),
            payment_url=result.url,
            final_pricing=retort.dump(pricing),
        )

    except Exception as e:
        ref = uuid.uuid4().hex[:12]
        logger.exception(
            "{} add_devices_payment_failed ref={} error={}",
            user.log,
            ref,
            e,
        )
        await notifier.notify_user(
            user,
            payload=MessagePayloadDto(
                i18n_key="ntf-subscription.payment-creation-failed",
                i18n_kwargs={"ref": ref},
            ),
        )
        raise


@inject
async def on_add_devices_click(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    device_addon_dao: FromDishka[DeviceAddonDao],
    payment_gateway_dao: FromDishka[PaymentGatewayDao],
    notifier: FromDishka[Notifier],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    addons = await device_addon_dao.get_active()
    gateways = await payment_gateway_dao.get_active()

    if not addons:
        logger.warning(f"{user.log} No device addons available")
        await notifier.notify_user(user, i18n_key="ntf-subscription.addons-unavailable")
        return

    if not gateways:
        logger.warning(f"{user.log} No active payment gateways")
        await notifier.notify_user(user, i18n_key="ntf-subscription.gateways-unavailable")
        return

    dialog_manager.dialog_data["purchase_type"] = PurchaseType.ADD_DEVICES
    dialog_manager.dialog_data.pop(CURRENT_DURATION_KEY, None)
    dialog_manager.dialog_data.pop(PAYMENT_CACHE_KEY, None)
    await dialog_manager.switch_to(state=Subscription.ADD_DEVICES_ADDON)


@inject
async def on_device_addon_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    selected_addon_id: int,
    device_addon_dao: FromDishka[DeviceAddonDao],
    payment_gateway_dao: FromDishka[PaymentGatewayDao],
    notifier: FromDishka[Notifier],
    retort: FromDishka[Retort],
    pricing_service: FromDishka[PricingService],
    create_payment: FromDishka[CreatePayment],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    addon = await device_addon_dao.get_by_id(selected_addon_id)

    if not addon:
        raise ValueError(f"Device addon '{selected_addon_id}' not found")

    logger.info(f"{user.log} Selected device addon +{addon.device_count}")
    dialog_manager.dialog_data[DeviceAddonDto.__name__] = retort.dump(addon)

    gateways = await payment_gateway_dao.get_active()
    if len(gateways) == 1:
        payment_data = await _create_payment_add_devices(
            dialog_manager=dialog_manager,
            device_addon=addon,
            gateway_type=gateways[0].type,
            retort=retort,
            payment_gateway_dao=payment_gateway_dao,
            notifier=notifier,
            pricing_service=pricing_service,
            create_payment=create_payment,
        )
        if payment_data:
            cache = _load_payment_data(dialog_manager)
            cache[_get_addon_cache_key(addon.device_count, gateways[0].type)] = payment_data
            _save_payment_data(dialog_manager, payment_data)
            dialog_manager.dialog_data[CURRENT_METHOD_KEY] = gateways[0].type
            await dialog_manager.switch_to(state=Subscription.CONFIRM)
        return

    await dialog_manager.switch_to(state=Subscription.PAYMENT_METHOD)


@inject
async def on_promocode_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    activate_promocode: FromDishka[ActivatePromocode],
    notifier: FromDishka[Notifier],
    i18n: FromDishka[TranslatorRunner],
    redis: FromDishka[Redis],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    if await is_rate_limited(redis, "promocode", user.telegram_id, 12):
        await notifier.notify_user(user, i18n_key="ntf-common.rate-limited")
        return

    code = message.text.strip() if message.text else ""

    result = await activate_promocode(user, ActivatePromocodeDto(code=code))

    kwargs = dict(result.i18n_kwargs or {})
    if result.success and result.i18n_key == "ntf-promocode.subscription-activated-success":
        if "plan_name" in kwargs:
            kwargs["plan_name"] = i18n.get(str(kwargs["plan_name"]))

    await notifier.notify_user(
        user,
        payload=MessagePayloadDto(i18n_key=result.i18n_key, i18n_kwargs=kwargs),
    )

    if result.success:
        await dialog_manager.switch_to(state=Subscription.MAIN)


@inject
async def on_purchase_type_select(
    purchase_type: PurchaseType,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    subscription_dao: FromDishka[SubscriptionDao],
    payment_gateway_dao: FromDishka[PaymentGatewayDao],
    notifier: FromDishka[Notifier],
    match_plan: FromDishka[MatchPlan],
    get_available_plans: FromDishka[GetAvailablePlans],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    current_subscription = await subscription_dao.get_current(user.telegram_id)
    if _trial_renew_blocked(current_subscription, purchase_type):
        logger.info(f"{user.log} Blocked RENEW: user is on trial subscription")
        await notifier.notify_user(user, i18n_key="ntf-subscription.trial-renew-not-allowed")
        return

    plans: list[PlanDto] = await get_available_plans.system(user)
    gateways = await payment_gateway_dao.get_active()
    dialog_manager.dialog_data["purchase_type"] = purchase_type
    dialog_manager.dialog_data.pop(CURRENT_DURATION_KEY, None)

    if not plans:
        logger.warning(f"{user.log} No available subscription plans")
        await notifier.notify_user(user, i18n_key="ntf-subscription.plans-unavailable")
        return

    if not gateways:
        logger.warning(f"{user.log} No active payment gateways")
        await notifier.notify_user(user, i18n_key="ntf-subscription.gateways-unavailable")
        return

    if purchase_type == PurchaseType.RENEW:
        if current_subscription:
            matched_plan = await match_plan.system(
                MatchPlanDto(plan_snapshot=current_subscription.plan_snapshot, plans=plans)
            )
            if matched_plan:
                dialog_manager.dialog_data[PlanDto.__name__] = retort.dump(matched_plan)
                dialog_manager.dialog_data["only_single_plan"] = True
                await dialog_manager.switch_to(state=Subscription.DURATION)
                return
            else:
                logger.warning(f"{user.log} Tried to renew, but no matching plan found")
                await notifier.notify_user(user, i18n_key="ntf-subscription.renew-plan-unavailable")
                return

    if len(plans) == 1:
        logger.info(f"{user.log} Auto-selected single plan '{plans[0].id}'")
        dialog_manager.dialog_data[PlanDto.__name__] = retort.dump(plans[0])
        dialog_manager.dialog_data["only_single_plan"] = True
        await dialog_manager.switch_to(state=Subscription.DURATION)
        return

    dialog_manager.dialog_data["only_single_plan"] = False
    await dialog_manager.switch_to(state=Subscription.PLANS)


@inject
async def on_subscription_plans(  # noqa: C901
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    subscription_dao: FromDishka[SubscriptionDao],
    payment_gateway_dao: FromDishka[PaymentGatewayDao],
    pricing_service: FromDishka[PricingService],
    notifier: FromDishka[Notifier],
    match_plan: FromDishka[MatchPlan],
    get_available_plans: FromDishka[GetAvailablePlans],
    create_payment: FromDishka[CreatePayment],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    logger.info(f"{user.log} Opened subscription plans menu")

    plans: list[PlanDto] = await get_available_plans.system(user)
    gateways = await payment_gateway_dao.get_active()

    if not callback.data:
        raise ValueError("Callback data is empty")

    purchase_type = PurchaseType(callback.data.removeprefix(PAYMENT_PREFIX))
    current_subscription = await subscription_dao.get_current(user.telegram_id)
    if _trial_renew_blocked(current_subscription, purchase_type):
        logger.info(f"{user.log} Blocked RENEW: user is on trial subscription")
        await notifier.notify_user(user, i18n_key="ntf-subscription.trial-renew-not-allowed")
        return

    dialog_manager.dialog_data["purchase_type"] = purchase_type

    dialog_manager.dialog_data.pop(CURRENT_DURATION_KEY, None)

    if not plans:
        logger.warning(f"{user.log} No available subscription plans")
        await notifier.notify_user(user, i18n_key="ntf-subscription.plans-unavailable")
        return

    if not gateways:
        logger.warning(f"{user.log} No active payment gateways")
        await notifier.notify_user(user, i18n_key="ntf-subscription.gateways-unavailable")
        return

    if purchase_type == PurchaseType.RENEW:
        if current_subscription:
            matched_plan = await match_plan.system(
                MatchPlanDto(plan_snapshot=current_subscription.plan_snapshot, plans=plans)
            )
            if matched_plan:
                dialog_manager.dialog_data[PlanDto.__name__] = retort.dump(matched_plan)
                dialog_manager.dialog_data["only_single_plan"] = True
                await dialog_manager.switch_to(state=Subscription.DURATION)
                return
            else:
                logger.warning(f"{user.log} Tried to renew, but no matching plan found")
                await notifier.notify_user(user, i18n_key="ntf-subscription.renew-plan-unavailable")
                return

    if len(plans) == 1:
        logger.info(f"{user.log} Auto-selected single plan '{plans[0].id}'")
        dialog_manager.dialog_data[PlanDto.__name__] = retort.dump(plans[0])
        dialog_manager.dialog_data["only_single_plan"] = True

        if len(plans[0].durations) == 1:
            logger.info(f"{user.log} Auto-selected duration '{plans[0].durations[0].days}'")
            dialog_manager.dialog_data["selected_duration"] = plans[0].durations[0].days
            dialog_manager.dialog_data["only_single_duration"] = True

            if len(gateways) == 1:
                logger.info(f"{user.log} Auto-selected payment method '{gateways[0].type}'")
                dialog_manager.dialog_data["selected_payment_method"] = gateways[0].type
                dialog_manager.dialog_data["only_single_payment_method"] = True

                payment_data = await _create_payment_and_get_data(
                    dialog_manager=dialog_manager,
                    plan=plans[0],
                    duration_days=plans[0].durations[0].days,
                    gateway_type=gateways[0].type,
                    retort=retort,
                    payment_gateway_dao=payment_gateway_dao,
                    notifier=notifier,
                    pricing_service=pricing_service,
                    create_payment=create_payment,
                )

                if payment_data:
                    _save_payment_data(dialog_manager, payment_data)

                await dialog_manager.switch_to(state=Subscription.CONFIRM)
                return

            await dialog_manager.switch_to(state=Subscription.PAYMENT_METHOD)
            return

        await dialog_manager.switch_to(state=Subscription.DURATION)
        return

    dialog_manager.dialog_data["only_single_plan"] = False
    dialog_manager.dialog_data["only_single_duration"] = False
    await dialog_manager.switch_to(state=Subscription.PLANS)


@inject
async def on_plan_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    selected_plan: int,
    retort: FromDishka[Retort],
    plan_dao: FromDishka[PlanDao],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    plan = await plan_dao.get_by_id(plan_id=selected_plan)

    if not plan:
        raise ValueError(f"Selected plan '{selected_plan}' not found")

    logger.info(f"{user.log} Selected plan '{plan.id}'")

    dialog_manager.dialog_data[PlanDto.__name__] = retort.dump(plan)
    dialog_manager.dialog_data.pop(PAYMENT_CACHE_KEY, None)
    dialog_manager.dialog_data.pop(CURRENT_DURATION_KEY, None)
    dialog_manager.dialog_data.pop(CURRENT_METHOD_KEY, None)

    if len(plan.durations) == 1:
        logger.info(f"{user.log} Auto-selected single duration '{plan.durations[0].days}'")
        dialog_manager.dialog_data["only_single_duration"] = True
        await on_duration_select(callback, widget, dialog_manager, plan.durations[0].days)  # type:ignore[no-untyped-call]
        return

    await dialog_manager.switch_to(state=Subscription.DURATION)


@inject
async def on_duration_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    selected_duration: int,
    retort: FromDishka[Retort],
    settings_dao: FromDishka[SettingsDao],
    payment_gateway_dao: FromDishka[PaymentGatewayDao],
    notifier: FromDishka[Notifier],
    pricing_service: FromDishka[PricingService],
    create_payment: FromDishka[CreatePayment],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    logger.info(f"{user.log} Selected subscription duration '{selected_duration}' days")
    dialog_manager.dialog_data[CURRENT_DURATION_KEY] = selected_duration

    raw_plan = dialog_manager.dialog_data.get(PlanDto.__name__)
    plan = retort.load(raw_plan, PlanDto)

    if not plan:
        raise ValueError("PlanDto not found in dialog data")

    settings = await settings_dao.get()
    gateways = await payment_gateway_dao.get_active()
    currency = settings.default_currency
    price = pricing_service.calculate(
        user,
        price=plan.get_duration(selected_duration).get_price(currency),  # type: ignore[union-attr]
        currency=currency,
    )
    dialog_manager.dialog_data["is_free"] = price.is_free

    if len(gateways) == 1 or price.is_free:
        selected_payment_method = gateways[0].type
        dialog_manager.dialog_data[CURRENT_METHOD_KEY] = selected_payment_method

        cache = _load_payment_data(dialog_manager)
        cache_key = _get_cache_key(selected_duration, selected_payment_method)

        if cache_key in cache:
            logger.info(f"{user.log} Re-selected same duration and single gateway")
            _save_payment_data(dialog_manager, cache[cache_key])
            await dialog_manager.switch_to(state=Subscription.CONFIRM)
            return

        logger.info(f"{user.log} Auto-selected single gateway '{selected_payment_method}'")

        payment_data = await _create_payment_and_get_data(
            dialog_manager=dialog_manager,
            plan=plan,
            duration_days=selected_duration,
            gateway_type=selected_payment_method,
            retort=retort,
            payment_gateway_dao=payment_gateway_dao,
            notifier=notifier,
            pricing_service=pricing_service,
            create_payment=create_payment,
        )

        if payment_data:
            cache[cache_key] = payment_data
            _save_payment_data(dialog_manager, payment_data)
            await dialog_manager.switch_to(state=Subscription.CONFIRM)
            return

    dialog_manager.dialog_data.pop(CURRENT_METHOD_KEY, None)
    await dialog_manager.switch_to(state=Subscription.PAYMENT_METHOD)


@inject
async def on_payment_method_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    selected_payment_method: PaymentGatewayType,
    retort: FromDishka[Retort],
    payment_gateway_dao: FromDishka[PaymentGatewayDao],
    notifier: FromDishka[Notifier],
    pricing_service: FromDishka[PricingService],
    create_payment: FromDishka[CreatePayment],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    logger.info(f"{user.log} Selected payment method '{selected_payment_method}'")

    dialog_manager.dialog_data[CURRENT_METHOD_KEY] = selected_payment_method
    cache = _load_payment_data(dialog_manager)
    purchase_type = dialog_manager.dialog_data.get("purchase_type")

    if purchase_type == PurchaseType.ADD_DEVICES:
        raw_addon = dialog_manager.dialog_data.get(DeviceAddonDto.__name__)
        addon = retort.load(raw_addon, DeviceAddonDto) if raw_addon else None
        if not addon:
            raise ValueError("DeviceAddonDto not found in dialog data")
        cache_key = _get_addon_cache_key(addon.device_count, selected_payment_method)
        if cache_key in cache:
            _save_payment_data(dialog_manager, cache[cache_key])
            await dialog_manager.switch_to(state=Subscription.CONFIRM)
            return
        payment_data = await _create_payment_add_devices(
            dialog_manager=dialog_manager,
            device_addon=addon,
            gateway_type=selected_payment_method,
            retort=retort,
            payment_gateway_dao=payment_gateway_dao,
            notifier=notifier,
            pricing_service=pricing_service,
            create_payment=create_payment,
        )
        if payment_data:
            cache[cache_key] = payment_data
            _save_payment_data(dialog_manager, payment_data)
        await dialog_manager.switch_to(state=Subscription.CONFIRM)
        return

    selected_duration = dialog_manager.dialog_data[CURRENT_DURATION_KEY]
    cache_key = _get_cache_key(selected_duration, selected_payment_method)

    if cache_key in cache:
        logger.info(f"{user.log} Re-selected same method and duration")
        _save_payment_data(dialog_manager, cache[cache_key])
        await dialog_manager.switch_to(state=Subscription.CONFIRM)
        return

    logger.info(f"{user.log} New combination. Creating new payment")

    raw_plan = dialog_manager.dialog_data.get(PlanDto.__name__)
    plan = retort.load(raw_plan, PlanDto)

    if not plan:
        raise ValueError("PlanDto not found in dialog data")

    payment_data = await _create_payment_and_get_data(
        dialog_manager=dialog_manager,
        plan=plan,
        duration_days=selected_duration,
        gateway_type=selected_payment_method,
        retort=retort,
        payment_gateway_dao=payment_gateway_dao,
        notifier=notifier,
        pricing_service=pricing_service,
        create_payment=create_payment,
    )

    if payment_data:
        cache[cache_key] = payment_data
        _save_payment_data(dialog_manager, payment_data)

    await dialog_manager.switch_to(state=Subscription.CONFIRM)


@inject
async def on_get_subscription(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    process_payment: FromDishka[ProcessPayment],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    payment_id = dialog_manager.dialog_data["payment_id"]
    logger.info(f"{user.log} Getted free subscription '{payment_id}'")
    await process_payment.system(ProcessPaymentDto(payment_id, TransactionStatus.COMPLETED))
