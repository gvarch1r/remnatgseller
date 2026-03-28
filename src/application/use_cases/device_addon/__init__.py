from typing import Final

from src.application.common import Interactor

from .commands.manage import ToggleDeviceAddonActive

DEVICE_ADDON_USE_CASES: Final[tuple[type[Interactor], ...]] = (ToggleDeviceAddonActive,)

__all__ = ["DEVICE_ADDON_USE_CASES", "ToggleDeviceAddonActive"]
