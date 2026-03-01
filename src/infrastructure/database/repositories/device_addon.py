from typing import Optional

from src.infrastructure.database.models.sql import DeviceAddon

from .base import BaseRepository


class DeviceAddonRepository(BaseRepository):
    async def get(self, addon_id: int) -> Optional[DeviceAddon]:
        return await self._get_one(DeviceAddon, DeviceAddon.id == addon_id)

    async def get_active(self) -> list[DeviceAddon]:
        return await self._get_many(
            DeviceAddon,
            DeviceAddon.is_active == True,  # noqa: E712
            order_by=DeviceAddon.order_index.asc(),
        )
