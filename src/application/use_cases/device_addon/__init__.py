from typing import Final

from src.application.common import Interactor

from .commands.create import CreateDeviceAddon
from .commands.manage import ToggleDeviceAddonActive

DEVICE_ADDON_USE_CASES: Final[tuple[type[Interactor], ...]] = (
    CreateDeviceAddon,
    ToggleDeviceAddonActive,
)

__all__ = ["DEVICE_ADDON_USE_CASES", "CreateDeviceAddon", "ToggleDeviceAddonActive"]
