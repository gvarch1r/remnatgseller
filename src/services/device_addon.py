from decimal import Decimal
from typing import Optional

from aiogram import Bot
from fluentogram import TranslatorHub
from loguru import logger
from redis.asyncio import Redis

from src.core.config import AppConfig
from src.core.enums import Currency
from src.infrastructure.database import UnitOfWork
from src.infrastructure.database.models.dto import DeviceAddonDto, DeviceAddonPriceDto
from src.infrastructure.database.models.sql import DeviceAddon, DeviceAddonPrice
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

    async def get_all(self) -> list[DeviceAddonDto]:
        async with self.uow:
            addons = await self.uow.repository.device_addons.get_all()
        return DeviceAddonDto.from_model_list(addons)

    async def get(self, addon_id: int) -> Optional[DeviceAddonDto]:
        async with self.uow:
            addon = await self.uow.repository.device_addons.get(addon_id)
        return DeviceAddonDto.from_model(addon)

    async def create(self, device_count: int, prices: dict[Currency, Decimal]) -> DeviceAddonDto:
        async with self.uow:
            max_idx = await self.uow.repository.device_addons.get_max_order_index()
            order_index = (max_idx or 0) + 1
            addon = DeviceAddon(
                device_count=device_count,
                order_index=order_index,
                is_active=True,
            )
            addon = await self.uow.repository.device_addons.create(addon)
            for currency, price in prices.items():
                addon.prices.append(
                    DeviceAddonPrice(device_addon_id=addon.id, currency=currency, price=price)
                )
            addon = await self.uow.repository.device_addons.update(addon)
        logger.info(f"Created device addon +{device_count} devices, id={addon.id}")
        return DeviceAddonDto.from_model(addon)

    async def update(
        self,
        addon_id: int,
        *,
        device_count: Optional[int] = None,
        is_active: Optional[bool] = None,
        prices: Optional[dict[Currency, Decimal]] = None,
    ) -> Optional[DeviceAddonDto]:
        async with self.uow:
            addon = await self.uow.repository.device_addons.get(addon_id)
            if not addon:
                return None
            if device_count is not None:
                addon.device_count = device_count
            if is_active is not None:
                addon.is_active = is_active
            if prices is not None:
                addon.prices.clear()
                for currency, price in prices.items():
                    addon.prices.append(
                        DeviceAddonPrice(device_addon_id=addon_id, currency=currency, price=price)
                    )
            addon = await self.uow.repository.device_addons.update(addon)
        logger.info(f"Updated device addon id={addon_id}")
        return DeviceAddonDto.from_model(addon)

    async def update_price(self, addon_id: int, currency: Currency, price: Decimal) -> bool:
        async with self.uow:
            addon = await self.uow.repository.device_addons.get(addon_id)
            if not addon:
                return False
            for p in addon.prices:
                if p.currency == currency:
                    p.price = price
                    await self.uow.repository.device_addons.update(addon)
                    return True
            addon.prices.append(
                DeviceAddonPrice(device_addon_id=addon_id, currency=currency, price=price)
            )
            await self.uow.repository.device_addons.update(addon)
        return True
