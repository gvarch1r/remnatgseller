from aiogram_dialog import Dialog, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Row, ScrollingGroup, Select, Start, SwitchTo
from aiogram_dialog.widgets.text import Format
from magic_filter import F

from src.bot.keyboards import main_menu_button
from src.bot.states import Dashboard, DashboardPromocodes
from src.bot.widgets import Banner, I18nFormat, IgnoreUpdate
from src.core.enums import BannerName, PromocodeAvailability, PromocodeRewardType

from .getters import (
    configurator_getter,
    list_getter,
    promocode_availabilities_getter,
    promocode_reward_getter,
    promocode_reward_types_getter,
    search_results_getter,
)
from .handlers import (
    on_active_toggle,
    on_confirm_promocode,
    on_promocode_availability_select,
    on_promocode_code_input,
    on_promocode_lifetime_input,
    on_promocode_max_activations_input,
    on_promocode_reward_input,
    on_promocode_reward_type_select,
    on_promocode_search,
    on_promocode_select,
)

promocodes = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocodes-main"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocodes-create"),
            id="create",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocodes-list"),
            id="list",
            state=DashboardPromocodes.LIST,
        ),
        SwitchTo(
            text=I18nFormat("btn-promocodes-search"),
            id="search",
            state=DashboardPromocodes.SEARCH,
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
    state=DashboardPromocodes.MAIN,
)

configurator = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-configurator"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocode-code"),
            id="code",
            state=DashboardPromocodes.CODE,
        ),
        SwitchTo(
            text=I18nFormat("btn-promocode-type"),
            id="type",
            state=DashboardPromocodes.TYPE,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocode-availability"),
            id="availability",
            state=DashboardPromocodes.AVAILABILITY,
        ),
        Button(
            text=I18nFormat("btn-promocode-active", is_active=F["is_active"]),
            id="active_toggle",
            on_click=on_active_toggle,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocode-reward"),
            id="reward",
            state=DashboardPromocodes.REWARD,
        ),
        SwitchTo(
            text=I18nFormat("btn-promocode-lifetime"),
            id="lifetime",
            state=DashboardPromocodes.LIFETIME,
        ),
        SwitchTo(
            text=I18nFormat("btn-promocode-activations"),
            id="activations",
            state=DashboardPromocodes.ACTIVATIONS,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocode-allowed"),
            id="allowed",
            state=DashboardPromocodes.ALLOWED,
            when=F["availability"] == PromocodeAvailability.ALLOWED,
        ),
    ),
    Row(
        Button(
            text=I18nFormat("btn-promocode-confirm"),
            id="confirm",
            on_click=on_confirm_promocode,
        ),
    ),
    Row(
        Start(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.MAIN,
            mode=StartMode.RESET_STACK,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.CONFIGURATOR,
    getter=configurator_getter,
)

promocodes_list = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocodes-list"),
    ScrollingGroup(
        Select(
            text=Format("{item[code]} ({item[reward_type]})"),
            id="promocode",
            item_id_getter=lambda item: item["id"],
            items="promocodes",
            type_factory=int,
            on_click=on_promocode_select,
        ),
        id="scroll",
        width=1,
        height=7,
        hide_on_single_page=True,
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.MAIN,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.LIST,
    getter=list_getter,
)

promocodes_search = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocodes-search"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.MAIN,
        ),
    ),
    MessageInput(func=on_promocode_search),
    IgnoreUpdate(),
    state=DashboardPromocodes.SEARCH,
)

promocodes_search_results = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocodes-search-results"),
    ScrollingGroup(
        Select(
            text=Format("{item[code]} ({item[reward_type]})"),
            id="promocode",
            item_id_getter=lambda item: item["id"],
            items="search_results",
            type_factory=int,
            on_click=on_promocode_select,
        ),
        id="scroll",
        width=1,
        height=7,
        hide_on_single_page=True,
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.MAIN,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.SEARCH_RESULTS,
    getter=search_results_getter,
)

promocode_code = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-code"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_promocode_code_input),
    IgnoreUpdate(),
    state=DashboardPromocodes.CODE,
)

promocode_type = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-type-select"),
    Column(
        Select(
            text=I18nFormat("btn-promocode-reward-type-choice", type=F["item"]),
            id="select_reward_type",
            item_id_getter=lambda item: item.value,
            items="reward_types",
            type_factory=PromocodeRewardType,
            on_click=on_promocode_reward_type_select,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.TYPE,
    getter=promocode_reward_types_getter,
)

promocode_availability = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-availability-select"),
    Column(
        Select(
            text=I18nFormat("btn-promocode-availability-choice", type=F["item"]),
            id="select_availability",
            item_id_getter=lambda item: item.value,
            items="availabilities",
            type_factory=PromocodeAvailability,
            on_click=on_promocode_availability_select,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.AVAILABILITY,
    getter=promocode_availabilities_getter,
)

promocode_reward = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-reward", promocode_type=F["reward_type"]),
    I18nFormat("msg-promocode-reward-numeric-hint", when=F["needs_numeric_reward"]),
    I18nFormat("msg-promocode-reward-subscription", when=~F["needs_numeric_reward"]),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_promocode_reward_input),
    IgnoreUpdate(),
    state=DashboardPromocodes.REWARD,
    getter=promocode_reward_getter,
)

promocode_lifetime = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-lifetime"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_promocode_lifetime_input),
    IgnoreUpdate(),
    state=DashboardPromocodes.LIFETIME,
)

promocode_activations = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-activations"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_promocode_max_activations_input),
    IgnoreUpdate(),
    state=DashboardPromocodes.ACTIVATIONS,
)

promocode_allowed = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-allowed-placeholder"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.ALLOWED,
)

router = Dialog(
    promocodes,
    promocodes_list,
    promocodes_search,
    promocodes_search_results,
    configurator,
    promocode_code,
    promocode_type,
    promocode_availability,
    promocode_reward,
    promocode_lifetime,
    promocode_activations,
    promocode_allowed,
)
