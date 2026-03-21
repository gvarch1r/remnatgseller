from typing import Optional, Tuple

from aiogram import Bot
from fluentogram import TranslatorHub
from loguru import logger
from redis.asyncio import Redis

from src.core.config import AppConfig
from src.core.enums import PromocodeRewardType
from src.infrastructure.database import UnitOfWork
from src.infrastructure.database.models.dto import PromocodeDto, UserDto
from src.infrastructure.redis import RedisRepository

from src.core.enums import AuditActionType

from .audit import AuditService
from .base import BaseService
from .user import UserService


class PromocodeService(BaseService):
    uow: UnitOfWork
    user_service: UserService
    audit_service: AuditService

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
    ) -> None:
        super().__init__(config, bot, redis_client, redis_repository, translator_hub)
        self.uow = uow
        self.user_service = user_service
        self.audit_service = audit_service

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

            if promocode.reward_type != PromocodeRewardType.PERSONAL_DISCOUNT:
                return False, "ntf-promocode-unsupported-type", None

            reward = promocode.reward or 0
            new_discount = max(user.personal_discount or 0, reward)

            await self.uow.repository.promocodes.create_activation(
                promocode.id,  # type: ignore[arg-type]
                user.telegram_id,
            )
            await self.uow.repository.users.update(
                user.telegram_id, personal_discount=new_discount
            )

        await self.user_service.clear_user_cache(user.telegram_id)
        await self.audit_service.log(
            user_telegram_id=user.telegram_id,
            action_type=AuditActionType.PROMOCODE_ACTIVATED,
            details=f"code={promocode.code} discount={reward}%",
        )
        logger.info(f"User {user.telegram_id} activated promocode '{promocode.code}'")
        return True, "ntf-promocode-activated-success", {"percent": reward}
