from aiogram_dialog import Dialog, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, ListGroup, Row, ScrollingGroup, SwitchTo
from magic_filter import F

from src.core.enums import BannerName
from src.telegram.keyboards import main_menu_button
from src.telegram.states import DashboardRemnashop, RemnashopDeviceAddons
from src.telegram.widgets import Banner, I18nFormat, IgnoreUpdate

from .getters import device_addons_admin_getter
from .handlers import on_device_addon_active_toggle, on_device_addon_row_click

main = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-device-addons-main", when=~F["addons_empty"]),
    I18nFormat("msg-device-addons-empty", when=F["addons_empty"]),
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
        SwitchTo(
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

router = Dialog(
    main,
)
