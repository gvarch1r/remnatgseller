from typing import Optional

from sqlalchemy import func, select

from src.infrastructure.database.models.sql import DeviceAddon, DeviceAddonPrice

from .base import BaseRepository


class DeviceAddonRepository(BaseRepository):
    async def get(self, addon_id: int) -> Optional[DeviceAddon]:
        return await self._get_one(DeviceAddon, DeviceAddon.id == addon_id)

    async def get_all(self) -> list[DeviceAddon]:
        return await self._get_many(
            DeviceAddon,
            order_by=DeviceAddon.order_index.asc(),
        )

    async def get_active(self) -> list[DeviceAddon]:
        return await self._get_many(
            DeviceAddon,
            DeviceAddon.is_active == True,  # noqa: E712
            order_by=DeviceAddon.order_index.asc(),
        )

    async def create(self, addon: DeviceAddon) -> DeviceAddon:
        return await self.create_instance(addon)

    async def update(self, addon: DeviceAddon) -> Optional[DeviceAddon]:
        return await self.merge_instance(addon)

    async def get_max_order_index(self) -> Optional[int]:
        return await self.session.scalar(select(func.max(DeviceAddon.order_index)))
