from typing import Protocol, runtime_checkable

from src.application.dto import DeviceAddonDto


@runtime_checkable
class DeviceAddonDao(Protocol):
    async def get_by_id(self, addon_id: int) -> DeviceAddonDto | None: ...

    async def get_active(self) -> list[DeviceAddonDto]: ...
