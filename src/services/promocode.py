from typing import Optional, Tuple

from aiogram import Bot
from sqlalchemy import delete
from fluentogram import TranslatorHub
from loguru import logger
from redis.asyncio import Redis

from src.core.config import AppConfig
from src.core.enums import PromocodeRewardType
from src.infrastructure.database import UnitOfWork
from src.infrastructure.database.models.dto import PromocodeDto, SubscriptionDto, UserDto
from src.infrastructure.database.models.sql.promocode import PromocodeActivation
from src.infrastructure.redis import RedisRepository

from src.core.enums import AuditActionType

from .audit import AuditService
from .base import BaseService
from .remnawave import RemnawaveService
from .subscription import SubscriptionService
from .user import UserService


class PromocodeService(BaseService):
    uow: UnitOfWork
    user_service: UserService
    audit_service: AuditService
    subscription_service: SubscriptionService
    remnawave_service: RemnawaveService

    def __init__(
        self,
        config: AppConfig,
        bot: Bot,
        redis_client: Redis,
        redis_repository: RedisRepository,
        translator_hub: TranslatorHub,
        #
        uow: UnitOfWork,
        user_service: UserService,
        audit_service: AuditService,
        subscription_service: SubscriptionService,
        remnawave_service: RemnawaveService,
    ) -> None:
        super().__init__(config, bot, redis_client, redis_repository, translator_hub)
        self.uow = uow
        self.user_service = user_service
        self.audit_service = audit_service
        self.subscription_service = subscription_service
        self.remnawave_service = remnawave_service

    async def create(self, promocode: PromocodeDto) -> PromocodeDto:
        from src.infrastructure.database.models.sql import Promocode

        db_promocode = Promocode(
            code=promocode.code,
            is_active=promocode.is_active,
            reward_type=promocode.reward_type,
            reward=promocode.reward if promocode.reward is not None else None,
            plan=promocode.plan.model_dump(mode="json") if promocode.plan else None,
            lifetime=promocode.lifetime if promocode.lifetime >= 0 else None,
            max_activations=promocode.max_activations if promocode.max_activations >= 0 else None,
        )

        async with self.uow:
            db_promocode = await self.uow.repository.promocodes.create(db_promocode)

        logger.info(f"Created promocode '{promocode.code}'")
        return PromocodeDto.from_model(db_promocode)  # type: ignore[return-value]

    async def get(self, promocode_id: int) -> Optional[PromocodeDto]:
        async with self.uow:
            db_promocode = await self.uow.repository.promocodes.get(promocode_id)

        if db_promocode:
            logger.debug(f"Retrieved promocode '{promocode_id}'")
        else:
            logger.warning(f"Promocode '{promocode_id}' not found")

        return PromocodeDto.from_model(db_promocode)

    async def get_by_code(self, promocode_code: str) -> Optional[PromocodeDto]:
        async with self.uow:
            db_promocode = await self.uow.repository.promocodes.get_by_code(promocode_code)

        if db_promocode:
            logger.debug(f"Retrieved promocode by code '{promocode_code}'")
        else:
            logger.warning(f"Promocode with code '{promocode_code}' not found")

        return PromocodeDto.from_model(db_promocode)

    async def search_by_code(self, query: str) -> list[PromocodeDto]:
        async with self.uow:
            db_promocodes = await self.uow.repository.promocodes.search_by_code(query)

        logger.debug(f"Searched promocodes by '{query}', found '{len(db_promocodes)}'")
        return PromocodeDto.from_model_list(db_promocodes)

    async def get_all(self) -> list[PromocodeDto]:
        async with self.uow:
            db_promocodes = await self.uow.repository.promocodes.get_all()

        logger.debug(f"Retrieved '{len(db_promocodes)}' promocodes")
        return PromocodeDto.from_model_list(db_promocodes)

    async def update(self, promocode: PromocodeDto) -> Optional[PromocodeDto]:
        # Не использовать changed_data: при from_model() в TrackableDto попадают все поля DTO,
        # включая availability / activations — колонок в promocodes нет → падение SQLAlchemy.
        update_data = {
            "code": promocode.code,
            "is_active": promocode.is_active,
            "reward_type": promocode.reward_type,
            "reward": promocode.reward if promocode.reward is not None else None,
            "plan": promocode.plan.model_dump(mode="json") if promocode.plan else None,
            "lifetime": promocode.lifetime if promocode.lifetime >= 0 else None,
            "max_activations": promocode.max_activations if promocode.max_activations >= 0 else None,
        }

        async with self.uow:
            db_updated_promocode = await self.uow.repository.promocodes.update(
                promocode_id=promocode.id,  # type: ignore[arg-type]
                **update_data,
            )

        if db_updated_promocode:
            logger.info(f"Updated promocode '{promocode.code}' successfully")
        else:
            logger.warning(
                f"Attempted to update promocode '{promocode.code}' "
                f"(ID: '{promocode.id}'), but promocode was not found or update failed"
            )

        return PromocodeDto.from_model(db_updated_promocode)

    async def delete(self, promocode_id: int) -> bool:
        async with self.uow:
            await self.uow.session.execute(
                delete(PromocodeActivation).where(
                    PromocodeActivation.promocode_id == promocode_id
                )
            )
            result = await self.uow.repository.promocodes.delete(promocode_id)

        if result:
            logger.info(f"Promocode '{promocode_id}' deleted successfully")
        else:
            logger.warning(
                f"Failed to delete promocode '{promocode_id}'. "
                f"Promocode not found or deletion failed"
            )

        return result

    async def filter_by_type(self, promocode_type: PromocodeRewardType) -> list[PromocodeDto]:
        async with self.uow:
            db_promocodes = await self.uow.repository.promocodes.filter_by_type(promocode_type)

        logger.debug(
            f"Filtered promocodes by type '{promocode_type}', found '{len(db_promocodes)}'"
        )
        return PromocodeDto.from_model_list(db_promocodes)

    async def filter_active(self, is_active: bool = True) -> list[PromocodeDto]:
        async with self.uow:
            db_promocodes = await self.uow.repository.promocodes.filter_active(is_active)

        logger.debug(f"Filtered active promocodes: '{is_active}', found '{len(db_promocodes)}'")
        return PromocodeDto.from_model_list(db_promocodes)

    async def activate_for_user(
        self, code: str, user: UserDto
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Activate promocode for user. Returns (success, i18n_key, optional i18n_kwargs).
        """
        code_clean = (code or "").strip().upper()
        if not code_clean:
            return False, "ntf-promocode-invalid-code", None

        async with self.uow:
            db_promocode = await self.uow.repository.promocodes.get_by_code(code_clean)

            if not db_promocode:
                logger.warning(f"Promocode '{code_clean}' not found")
                return False, "ntf-promocode-not-found", None

            promocode = PromocodeDto.from_model(db_promocode)
            if not promocode or not promocode.is_active:
                return False, "ntf-promocode-not-found", None

            if promocode.is_expired:
                return False, "ntf-promocode-expired", None

            activations_count = await self.uow.repository.promocodes.count_activations(
                promocode.id  # type: ignore[arg-type]
            )
            if promocode.max_activations is not None and promocode.max_activations >= 0:
                if activations_count >= promocode.max_activations:
                    return False, "ntf-promocode-depleted", None

            already_activated = await self.uow.repository.promocodes.has_user_activated(
                user.telegram_id, promocode.id  # type: ignore[arg-type]
            )
            if already_activated:
                return False, "ntf-promocode-already-activated", None

            discount_applied = False
            reward_percent = 0

            if promocode.reward_type == PromocodeRewardType.PERSONAL_DISCOUNT:
                reward_percent = promocode.reward or 0
                new_discount = max(user.personal_discount or 0, reward_percent)
                await self.uow.repository.promocodes.create_activation(
                    promocode.id,  # type: ignore[arg-type]
                    user.telegram_id,
                )
                await self.uow.repository.users.update(
                    user.telegram_id, personal_discount=new_discount
                )
                discount_applied = True

            elif promocode.reward_type == PromocodeRewardType.PURCHASE_DISCOUNT:
                reward_percent = promocode.reward or 0
                new_discount = max(user.purchase_discount or 0, reward_percent)
                await self.uow.repository.promocodes.create_activation(
                    promocode.id,  # type: ignore[arg-type]
                    user.telegram_id,
                )
                await self.uow.repository.users.update(
                    user.telegram_id, purchase_discount=new_discount
                )
                discount_applied = True

        if discount_applied:
            await self.user_service.clear_user_cache(user.telegram_id)
            await self.audit_service.log(
                user_telegram_id=user.telegram_id,
                action_type=AuditActionType.PROMOCODE_ACTIVATED,
                details=f"code={promocode.code} discount={reward_percent}%",
            )
            logger.info(f"User {user.telegram_id} activated promocode '{promocode.code}' (discount)")
            return True, "ntf-promocode-activated-success", {"percent": reward_percent}

        if promocode.reward_type == PromocodeRewardType.SUBSCRIPTION:
            if not promocode.plan:
                return False, "ntf-promocode-subscription-plan-required", None

            plan_snap = promocode.plan
            try:
                fresh_user = await self.user_service.get(user.telegram_id)
                if not fresh_user:
                    return False, "ntf-promocode-not-found", None

                current_sub = await self.subscription_service.get_current(user.telegram_id)
                if current_sub:
                    remna_user = await self.remnawave_service.updated_user(
                        user=fresh_user,
                        uuid=current_sub.user_remna_id,
                        plan=plan_snap,
                        reset_traffic=True,
                    )
                else:
                    remna_user = await self.remnawave_service.create_user(
                        user=fresh_user, plan=plan_snap
                    )

                new_subscription = SubscriptionDto(
                    user_remna_id=remna_user.uuid,
                    status=remna_user.status,
                    traffic_limit=plan_snap.traffic_limit,
                    device_limit=plan_snap.device_limit,
                    traffic_limit_strategy=plan_snap.traffic_limit_strategy,
                    tag=plan_snap.tag,
                    internal_squads=plan_snap.internal_squads,
                    external_squad=plan_snap.external_squad,
                    expire_at=remna_user.expire_at,
                    url=remna_user.subscription_url,
                    plan=plan_snap,
                )
                await self.subscription_service.create(fresh_user, new_subscription)
            except Exception as exc:
                logger.exception(
                    f"User {user.telegram_id} failed subscription promocode '{promocode.code}': {exc}"
                )
                return False, "ntf-promocode-subscription-activate-failed", None

            async with self.uow:
                await self.uow.repository.promocodes.create_activation(
                    promocode.id,  # type: ignore[arg-type]
                    user.telegram_id,
                )

            await self.user_service.clear_user_cache(user.telegram_id)
            await self.audit_service.log(
                user_telegram_id=user.telegram_id,
                action_type=AuditActionType.PROMOCODE_ACTIVATED,
                details=f"code={promocode.code} subscription plan={plan_snap.name}",
            )
            logger.info(
                f"User {user.telegram_id} activated promocode '{promocode.code}' (subscription)"
            )
            return True, "ntf-promocode-subscription-activated-success", {"plan_name": plan_snap.name}

        return False, "ntf-promocode-unsupported-type", None
