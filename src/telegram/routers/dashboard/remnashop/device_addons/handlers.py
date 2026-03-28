from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from loguru import logger

from src.application.dto import UserDto
from src.application.use_cases.device_addon.commands.manage import ToggleDeviceAddonActive
from src.core.constants import USER_KEY


async def on_device_addon_row_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    del button, dialog_manager
    await callback.answer()


@inject
async def on_device_addon_active_toggle(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    toggle_device_addon_active: FromDishka[ToggleDeviceAddonActive],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    addon_id = int(dialog_manager.item_id)  # type: ignore[attr-defined]
    logger.info(f"{user.log} Toggle device addon active id={addon_id}")
    await toggle_device_addon_active(user, addon_id)
    await dialog_manager.show()
