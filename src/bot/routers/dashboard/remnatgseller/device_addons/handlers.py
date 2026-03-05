from decimal import Decimal

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode, StartMode, SubManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from loguru import logger

from src.bot.states import DashboardRemnatgseller, RemnatgsellerDeviceAddons
from src.core.constants import USER_KEY
from src.core.enums import Currency
from src.core.utils.adapter import DialogDataAdapter
from src.core.utils.formatters import format_user_log as log
from src.core.utils.message_payload import MessagePayload
from src.core.utils.validators import parse_int
from src.infrastructure.database.models.dto import DeviceAddonDto, UserDto
from src.services.device_addon import DeviceAddonService
from src.services.notification import NotificationService
from src.services.pricing import PricingService


async def on_add_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data.pop("deviceaddondto", None)
    await dialog_manager.switch_to(state=RemnatgsellerDeviceAddons.ADD)


@inject
async def on_addon_select(
    callback: CallbackQuery,
    widget: Button,
    sub_manager: SubManager,
    device_addon_service: FromDishka[DeviceAddonService],
) -> None:
    user: UserDto = sub_manager.middleware_data[USER_KEY]
    addon_id = int(sub_manager.item_id)
    addon = await device_addon_service.get(addon_id)

    if not addon:
        raise ValueError(f"Addon '{addon_id}' not found")

    logger.info(f"{log(user)} Selected device addon id={addon_id}")
    adapter = DialogDataAdapter(sub_manager.manager)
    adapter.save(addon)
    await sub_manager.switch_to(state=RemnatgsellerDeviceAddons.EDIT)


@inject
async def on_active_toggle(
    callback: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    device_addon_service: FromDishka[DeviceAddonService],
) -> None:
    user: UserDto = manager.middleware_data[USER_KEY]
    addon_id = getattr(manager, "item_id", None)
    if not addon_id:
        adapter = DialogDataAdapter(manager)
        addon = adapter.load(DeviceAddonDto)
        if not addon:
            raise ValueError("DeviceAddonDto not found")
        addon_id = addon.id
    else:
        addon_id = int(addon_id)

    addon = await device_addon_service.get(addon_id)
    if not addon:
        raise ValueError(f"Addon {addon_id} not found")

    addon.is_active = not addon.is_active
    await device_addon_service.update(addon_id, is_active=addon.is_active)
    adapter = DialogDataAdapter(manager)
    adapter.save(addon)
    logger.info(f"{log(user)} Toggled addon id={addon_id} active={addon.is_active}")


@inject
async def on_currency_select(
    callback: CallbackQuery,
    widget: Select[Currency],
    dialog_manager: DialogManager,
    selected_currency: Currency,
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    dialog_manager.dialog_data["selected_currency"] = selected_currency.value
    logger.info(f"{log(user)} Selected currency '{selected_currency}' for price edit")
    await dialog_manager.switch_to(state=RemnatgsellerDeviceAddons.PRICE)


@inject
async def on_price_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    device_addon_service: FromDishka[DeviceAddonService],
    notification_service: FromDishka[NotificationService],
    pricing_service: FromDishka[PricingService],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    adapter = DialogDataAdapter(dialog_manager)
    addon = adapter.load(DeviceAddonDto)
    selected = dialog_manager.dialog_data.get("selected_currency")

    if not addon or not selected:
        await dialog_manager.switch_to(state=RemnatgsellerDeviceAddons.EDIT)
        return

    if message.text is None:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-plan-invalid-number"),
        )
        return

    currency = Currency(selected)
    try:
        new_price = pricing_service.parse_price(message.text, currency)
    except ValueError:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-plan-invalid-number"),
        )
        return

    await device_addon_service.update_price(addon.id, currency, new_price)
    addon = await device_addon_service.get(addon.id)
    if addon:
        adapter.save(addon)
    logger.info(f"{log(user)} Updated addon {addon.id} price {currency}={new_price}")
    await dialog_manager.switch_to(state=RemnatgsellerDeviceAddons.EDIT)


@inject
async def on_device_count_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    device_addon_service: FromDishka[DeviceAddonService],
    notification_service: FromDishka[NotificationService],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    adapter = DialogDataAdapter(dialog_manager)
    addon = adapter.load(DeviceAddonDto)

    if message.text is None:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-plan-invalid-number"),
        )
        return

    device_count = parse_int(message.text)
    if device_count is None or device_count < 1 or device_count > 10:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-plan-invalid-number"),
        )
        return

    if addon:
        await device_addon_service.update(addon.id, device_count=device_count)
        addon = await device_addon_service.get(addon.id)
        if addon:
            adapter.save(addon)
        logger.info(f"{log(user)} Updated addon {addon.id} device_count={device_count}")
    else:
        prices = {
            Currency.XTR: Decimal(device_count * 50),
            Currency.USD: Decimal(device_count * 0.5),
            Currency.RUB: Decimal(device_count * 50),
        }
        new_addon = await device_addon_service.create(device_count, prices)
        logger.info(f"{log(user)} Created addon +{device_count} id={new_addon.id}")
        adapter.save(new_addon)

    await dialog_manager.switch_to(state=RemnatgsellerDeviceAddons.EDIT)
