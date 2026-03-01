from aiogram import Bot
from fluentogram import TranslatorHub
from redis.asyncio import Redis

from src.core.config import AppConfig
from src.infrastructure.database import UnitOfWork
from src.infrastructure.database.models.dto import DeviceAddonDto
from src.infrastructure.redis import RedisRepository

from .base import BaseService


class DeviceAddonService(BaseService):
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

    async def get_active(self) -> list[DeviceAddonDto]:
        async with self.uow:
            addons = await self.uow.repository.device_addons.get_active()
        return DeviceAddonDto.from_model_list(addons)
