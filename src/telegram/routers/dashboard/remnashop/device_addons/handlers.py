from decimal import Decimal, InvalidOperation

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from loguru import logger

from src.application.common import Notifier
from src.application.dto import CreateDeviceAddonDto, UserDto
from src.application.use_cases.device_addon.commands.create import CreateDeviceAddon
from src.application.use_cases.device_addon.commands.delete import DeleteDeviceAddon
from src.application.use_cases.device_addon.commands.manage import ToggleDeviceAddonActive
from src.telegram.utils import is_double_click
from src.core.constants import USER_KEY
from src.core.enums import Currency
from src.telegram.states import RemnashopDeviceAddons


async def on_device_addon_row_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    del button, dialog_manager
    await callback.answer()


@inject
async def on_device_addon_delete_from_list(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    notifier: FromDishka[Notifier],
    delete_device_addon: FromDishka[DeleteDeviceAddon],
) -> None:
    del widget
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    addon_id = int(dialog_manager.item_id)  # type: ignore[attr-defined]

    if is_double_click(dialog_manager, key=f"delete_device_addon_{addon_id}", cooldown=10):
        try:
            await delete_device_addon(user, addon_id)
        except ValueError:
            await notifier.notify_user(user, i18n_key="ntf-error.unknown")
            await dialog_manager.show()
            return
        await notifier.notify_user(user, i18n_key="ntf-device-addon.deleted")
        await dialog_manager.show()
        return

    await notifier.notify_user(user, i18n_key="ntf-common.double-click-confirm")
    logger.debug(f"{user.log} Delete device addon id={addon_id} (awaiting confirmation)")


async def on_cancel_device_addon_add(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    del button
    dialog_manager.dialog_data.pop("addon_device_count", None)
    await callback.answer()
    await dialog_manager.switch_to(state=RemnashopDeviceAddons.MAIN)


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


def _parse_device_addon_prices(text: str) -> dict[Currency, Decimal] | None:
    result: dict[Currency, Decimal] = {}
    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            return None
        code, amount_raw = parts[0], parts[1]
        try:
            currency = Currency(code.upper())
        except ValueError:
            return None
        if currency in result:
            return None
        try:
            price = Decimal(amount_raw.replace(",", "."))
        except InvalidOperation:
            return None
        if price <= 0:
            return None
        result[currency] = price
    return result if result else None


@inject
async def on_device_addon_count_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    notifier: FromDishka[Notifier],
) -> None:
    del widget
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await notifier.notify_user(user, i18n_key="ntf-common.invalid-value")
        return
    n = int(raw)
    if n < 1:
        await notifier.notify_user(user, i18n_key="ntf-common.invalid-value")
        return
    dialog_manager.dialog_data["addon_device_count"] = n
    await dialog_manager.switch_to(state=RemnashopDeviceAddons.ADD_PRICES)


@inject
async def on_device_addon_prices_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    notifier: FromDishka[Notifier],
    create_device_addon: FromDishka[CreateDeviceAddon],
) -> None:
    del widget
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    parsed = _parse_device_addon_prices(message.text or "")
    if parsed is None:
        await notifier.notify_user(user, i18n_key="ntf-device-addon.prices-invalid")
        return
    count = dialog_manager.dialog_data.get("addon_device_count")
    if not isinstance(count, int) or count < 1:
        await dialog_manager.switch_to(state=RemnashopDeviceAddons.MAIN)
        return
    await create_device_addon(user, CreateDeviceAddonDto(device_count=count, prices=parsed))
    dialog_manager.dialog_data.pop("addon_device_count", None)
    await notifier.notify_user(user, i18n_key="ntf-device-addon.created")
    await dialog_manager.switch_to(state=RemnashopDeviceAddons.MAIN)
