from aiogram import Bot
from fluentogram import TranslatorHub
from loguru import logger
from redis.asyncio import Redis

from src.core.config import AppConfig
from src.core.enums import AuditActionType
from src.infrastructure.database import UnitOfWork
from src.infrastructure.redis import RedisRepository

from .base import BaseService


class AuditService(BaseService):
    uow: UnitOfWork

    def __init__(
        self,
        config: AppConfig,
        bot: Bot,
        redis_client: Redis,
        redis_repository: RedisRepository,
        translator_hub: TranslatorHub,
        uow: UnitOfWork,
    ) -> None:
        super().__init__(config, bot, redis_client, redis_repository, translator_hub)
        self.uow = uow

    async def log(
        self,
        user_telegram_id: int,
        action_type: AuditActionType,
        details: str = "",
        actor_telegram_id: int | None = None,
    ) -> None:
        async with self.uow:
            await self.uow.repository.audit_logs.create(
                user_telegram_id=user_telegram_id,
                action_type=action_type,
                details=details,
                actor_telegram_id=actor_telegram_id,
            )
        logger.debug(
            f"Audit: user={user_telegram_id} action={action_type.value} "
            f"actor={actor_telegram_id} details={details[:50] if len(details) > 50 else details}..."
        )

    async def get_by_user(
        self,
        user_telegram_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        async with self.uow:
            logs = await self.uow.repository.audit_logs.get_by_user(
                user_telegram_id=user_telegram_id,
                limit=limit,
                offset=offset,
            )
        return [
            {
                "action_type": log.action_type.value,
                "details": log.details,
                "created_at": log.created_at.strftime("%d.%m.%Y %H:%M") if log.created_at else "",
                "actor_telegram_id": log.actor_telegram_id,
            }
            for log in logs
        ]

    async def count_by_user(self, user_telegram_id: int) -> int:
        async with self.uow:
            return await self.uow.repository.audit_logs.count_by_user(user_telegram_id)
