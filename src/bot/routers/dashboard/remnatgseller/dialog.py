from aiogram_dialog import Dialog, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, ListGroup, Row, Start, SwitchTo
from aiogram_dialog.widgets.text import Format
from magic_filter import F

from src.bot.keyboards import main_menu_button
from src.bot.routers.extra.test import show_dev_popup
from src.bot.states import (
    Dashboard,
    DashboardRemnatgseller,
    DashboardUsers,
    RemnatgsellerGateways,
    RemnatgsellerNotifications,
    RemnatgsellerPlans,
    RemnatgsellerReferral,
)
from src.bot.widgets import Banner, I18nFormat, IgnoreUpdate
from src.core.enums import BannerName

from .getters import admins_getter, remnatgseller_getter
from .handlers import on_logs_request, on_user_role_remove, on_user_select

remnatgseller = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-remnatgseller-main"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-remnatgseller-admins"),
            id="admins",
            state=DashboardRemnatgseller.ADMINS,
        ),
    ),
    Row(
        Start(
            text=I18nFormat("btn-remnatgseller-gateways"),
            id="gateways",
            state=RemnatgsellerGateways.MAIN,
        ),
    ),
    Row(
        Start(
            text=I18nFormat("btn-remnatgseller-referral"),
            id="referral",
            state=RemnatgsellerReferral.MAIN,
        ),
        Button(
            text=I18nFormat("btn-remnatgseller-advertising"),
            id="advertising",
            # state=DashboardRemnatgseller.ADVERTISING,
            on_click=show_dev_popup,
        ),
    ),
    Row(
        Start(
            text=I18nFormat("btn-remnatgseller-plans"),
            id="plans",
            state=RemnatgsellerPlans.MAIN,
            mode=StartMode.RESET_STACK,
        ),
        Start(
            text=I18nFormat("btn-remnatgseller-notifications"),
            id="notifications",
            state=RemnatgsellerNotifications.MAIN,
        ),
    ),
    Row(
        Button(
            text=I18nFormat("btn-remnatgseller-logs"),
            id="logs",
            on_click=on_logs_request,
        ),
        Start(
            text=I18nFormat("btn-remnatgseller-audit"),
            id="audit",
            state=DashboardUsers.MAIN,
            mode=StartMode.RESET_STACK,
        ),
    ),
    Row(
        Start(
            text=I18nFormat("btn-back"),
            id="back",
            state=Dashboard.MAIN,
            mode=StartMode.RESET_STACK,
        ),
        *main_menu_button,
    ),
    IgnoreUpdate(),
    state=DashboardRemnatgseller.MAIN,
    getter=remnatgseller_getter,
)

admins = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-admins-main"),
    ListGroup(
        Row(
            Button(
                text=Format("{item[user_id]} ({item[user_name]})"),
                id="select_user",
                on_click=on_user_select,
            ),
            Button(
                text=Format("❌"),
                id="remove_role",
                on_click=on_user_role_remove,
                when=F["item"]["deletable"],
            ),
        ),
        id="admins_list",
        item_id_getter=lambda item: item["user_id"],
        items="admins",
    ),
    Row(
        Start(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardRemnatgseller.MAIN,
            mode=StartMode.RESET_STACK,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardRemnatgseller.ADMINS,
    getter=admins_getter,
)

router = Dialog(
    remnatgseller,
    admins,
)
