from decimal import Decimal
from typing import Protocol, runtime_checkable

from src.application.dto import DeviceAddonDto
from src.core.enums import Currency


@runtime_checkable
class DeviceAddonDao(Protocol):
    async def get_by_id(self, addon_id: int) -> DeviceAddonDto | None: ...

    async def get_active(self) -> list[DeviceAddonDto]: ...

    async def list_all(self) -> list[DeviceAddonDto]: ...

    async def toggle_active(self, addon_id: int) -> bool: ...

    async def create(
        self,
        device_count: int,
        prices: dict[Currency, Decimal],
    ) -> DeviceAddonDto: ...

    async def delete(self, addon_id: int) -> bool: ...
