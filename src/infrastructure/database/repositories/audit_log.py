from src.core.enums import AuditActionType
from src.infrastructure.database.models.sql import AuditLog

from .base import BaseRepository


class AuditLogRepository(BaseRepository):
    async def create(
        self,
        user_telegram_id: int,
        action_type: AuditActionType,
        details: str = "",
        actor_telegram_id: int | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_telegram_id=user_telegram_id,
            actor_telegram_id=actor_telegram_id,
            action_type=action_type,
            details=details,
        )
        return await self.create_instance(log)

    async def get_by_user(
        self,
        user_telegram_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        return await self._get_many(
            AuditLog,
            AuditLog.user_telegram_id == user_telegram_id,
            order_by=AuditLog.created_at.desc(),
            limit=limit,
            offset=offset,
        )

    async def count_by_user(self, user_telegram_id: int) -> int:
        return await self._count(AuditLog, AuditLog.user_telegram_id == user_telegram_id)
