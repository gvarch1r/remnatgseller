from aiogram_dialog import Dialog, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Column,
    ListGroup,
    Row,
    Select,
    Start,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Format
from magic_filter import F

from src.bot.keyboards import main_menu_button
from src.bot.states import DashboardRemnatgseller, RemnatgsellerDeviceAddons
from src.bot.widgets import Banner, I18nFormat, IgnoreUpdate
from src.core.enums import BannerName, Currency

from .getters import addons_getter, edit_getter, price_getter
from .handlers import (
    on_add_click,
    on_addon_select,
    on_active_toggle,
    on_currency_select,
    on_device_count_input,
    on_price_input,
)

addons_main = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-device-addons-main"),
    Row(
        Button(
            text=I18nFormat("btn-device-addons-create"),
            id="create",
            on_click=on_add_click,
        ),
    ),
    ListGroup(
        Row(
            Button(
                text=Format("+{item[device_count]} — {item[prices_str]}"),
                id="addon",
                on_click=on_addon_select,
            ),
            Button(
                text=I18nFormat("btn-device-addon-active", is_active=F["item"]["is_active"]),
                id="active_toggle",
                on_click=on_active_toggle,
            ),
        ),
        id="addons_list",
        item_id_getter=lambda item: str(item["id"]),
        items="addons",
    ),
    Row(
        Start(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardRemnatgseller.MAIN,
            mode=StartMode.RESET_STACK,
        ),
        *main_menu_button,
    ),
    IgnoreUpdate(),
    state=RemnatgsellerDeviceAddons.MAIN,
    getter=addons_getter,
)

addons_add = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-device-addons-add"),
    MessageInput(func=on_device_count_input),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerDeviceAddons.MAIN,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerDeviceAddons.ADD,
)

addons_edit = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-device-addons-edit", device_count=F["addon"]["device_count"]),
    Row(
        Button(
            text=I18nFormat("btn-device-addon-active", is_active=F["addon"]["is_active"]),
            id="active_toggle",
            on_click=on_active_toggle,
        ),
    ),
    I18nFormat("msg-device-addons-device-count-hint"),
    MessageInput(func=on_device_count_input),
    I18nFormat("msg-device-addons-prices"),
    Column(
        Select(
            text=Format("{item[symbol]} {item[currency]}"),
            id="currency",
            item_id_getter=lambda item: item["currency"],
            items="currency_list",
            type_factory=Currency,
            on_click=on_currency_select,
        ),
    ),
    Row(
        Start(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerDeviceAddons.MAIN,
            mode=StartMode.RESET_STACK,
        ),
        *main_menu_button,
    ),
    IgnoreUpdate(),
    state=RemnatgsellerDeviceAddons.EDIT,
    getter=edit_getter,
)

addons_price = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-device-addons-price", currency=F["currency"], current=F["current_price"]),
    MessageInput(func=on_price_input),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerDeviceAddons.EDIT,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerDeviceAddons.PRICE,
    getter=price_getter,
)

router = Dialog(
    addons_main,
    addons_add,
    addons_edit,
    addons_price,
)
