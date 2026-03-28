from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, ListGroup, Row, ScrollingGroup, Start, SwitchTo
from aiogram_dialog.widgets.style import Style
from magic_filter import F

from src.core.enums import BannerName
from src.telegram.keyboards import main_menu_button
from src.telegram.states import DashboardRemnashop, RemnashopDeviceAddons
from src.telegram.widgets import Banner, I18nFormat, IgnoreUpdate

from .getters import device_addon_add_prices_getter, device_addons_admin_getter
from .handlers import (
    on_cancel_device_addon_add,
    on_device_addon_active_toggle,
    on_device_addon_count_input,
    on_device_addon_delete_from_list,
    on_device_addon_prices_input,
    on_device_addon_row_click,
)

main = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-device-addons-admin"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-device-addon.add"),
            id="add_package",
            state=RemnashopDeviceAddons.ADD_DEVICE_COUNT,
            style=Style(ButtonStyle.SUCCESS),
        ),
    ),
    ScrollingGroup(
        ListGroup(
            Row(
                Button(
                    text=I18nFormat(
                        "btn-device-addon.row",
                        device_count=F["item"]["device_count"],
                        summary=F["item"]["summary"],
                    ),
                    id="addon_row",
                    on_click=on_device_addon_row_click,
                ),
                Button(
                    text=I18nFormat(
                        "btn-device-addon.active",
                        is_active=F["item"]["is_active"],
                    ),
                    id="toggle_active",
                    on_click=on_device_addon_active_toggle,
                ),
                Button(
                    text=I18nFormat("btn-device-addon.delete-list"),
                    id="delete_addon",
                    on_click=on_device_addon_delete_from_list,
                    style=Style(ButtonStyle.DANGER),
                ),
            ),
            id="device_addons_list",
            item_id_getter=lambda item: item["id"],
            items="device_addons",
        ),
        id="scroll_addons",
        width=1,
        height=8,
        hide_on_single_page=True,
        when=~F["addons_empty"],
    ),
    Row(
        Start(
            text=I18nFormat("btn-back.general"),
            id="back_remnashop",
            state=DashboardRemnashop.MAIN,
            mode=StartMode.RESET_STACK,
        ),
        *main_menu_button,
    ),
    IgnoreUpdate(),
    state=RemnashopDeviceAddons.MAIN,
    getter=device_addons_admin_getter,
)

add_device_count = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-device-addons-add-count"),
    Row(
        Button(
            text=I18nFormat("btn-back.general"),
            id="cancel_add_count",
            on_click=on_cancel_device_addon_add,
        ),
    ),
    MessageInput(func=on_device_addon_count_input),
    IgnoreUpdate(),
    state=RemnashopDeviceAddons.ADD_DEVICE_COUNT,
)

add_prices = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-device-addons-add-prices"),
    Row(
        Button(
            text=I18nFormat("btn-back.general"),
            id="cancel_add_prices",
            on_click=on_cancel_device_addon_add,
        ),
    ),
    MessageInput(func=on_device_addon_prices_input),
    IgnoreUpdate(),
    state=RemnashopDeviceAddons.ADD_PRICES,
    getter=device_addon_add_prices_getter,
)

router = Dialog(
    main,
    add_device_count,
    add_prices,
)
