from typing import Final

from src.application.common import Interactor

from .commands.create import CreateDeviceAddon
from .commands.delete import DeleteDeviceAddon
from .commands.manage import ToggleDeviceAddonActive

DEVICE_ADDON_USE_CASES: Final[tuple[type[Interactor], ...]] = (
    CreateDeviceAddon,
    DeleteDeviceAddon,
    ToggleDeviceAddonActive,
)

__all__ = [
    "DEVICE_ADDON_USE_CASES",
    "CreateDeviceAddon",
    "DeleteDeviceAddon",
    "ToggleDeviceAddonActive",
]
