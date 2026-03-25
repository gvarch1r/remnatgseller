from aiogram import F
from aiogram.enums import ButtonStyle
from aiogram_dialog import Dialog, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Row, ScrollingGroup, Select, Start, SwitchTo
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Format

from src.core.enums import BannerName, PromocodeRewardType
from src.telegram.keyboards import back_main_menu_button
from src.telegram.states import Dashboard, DashboardPromocodes
from src.telegram.widgets import Banner, I18nFormat, IgnoreUpdate

from .getters import (
    configurator_getter,
    list_getter,
    promocode_delete_confirm_getter,
    promocode_plan_duration_getter,
    promocode_plan_pick_getter,
    promocode_reward_getter,
    promocode_reward_types_getter,
    search_results_getter,
)
from .handlers import (
    on_active_toggle,
    on_confirm_promocode,
    on_create_promocode_click,
    on_promocode_code_input,
    on_promocode_delete_confirmed,
    on_promocode_lifetime_input,
    on_promocode_max_activations_input,
    on_promocode_reward_duration_select,
    on_promocode_reward_input,
    on_promocode_reward_plan_select,
    on_promocode_reward_type_select,
    on_promocode_search,
    on_promocode_select,
)

promocodes_main = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocodes-main"),
    Row(
        Button(
            text=I18nFormat("btn-promocodes-create"),
            id="promocodes_create",
            on_click=on_create_promocode_click,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocodes-list"),
            id="promocodes_list",
            state=DashboardPromocodes.LIST,
        ),
        SwitchTo(
            text=I18nFormat("btn-promocodes-search"),
            id="promocodes_search",
            state=DashboardPromocodes.SEARCH,
        ),
    ),
    Row(
        Start(
            text=I18nFormat("btn-back.general"),
            id="promocodes_back_dash",
            state=Dashboard.MAIN,
            mode=StartMode.RESET_STACK,
        ),
    ),
    *back_main_menu_button,
    IgnoreUpdate(),
    state=DashboardPromocodes.MAIN,
)

configurator = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-configurator"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocode.code"),
            id="promo_code",
            state=DashboardPromocodes.CODE,
        ),
        SwitchTo(
            text=I18nFormat("btn-promocode.type"),
            id="promo_type",
            state=DashboardPromocodes.TYPE,
        ),
    ),
    Row(
        Button(
            text=I18nFormat("btn-promocode.active", is_active=F["is_active"]),
            id="promo_active_toggle",
            on_click=on_active_toggle,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocode.reward"),
            id="promo_reward",
            state=DashboardPromocodes.REWARD,
        ),
        SwitchTo(
            text=I18nFormat("btn-promocode.lifetime"),
            id="promo_lifetime",
            state=DashboardPromocodes.LIFETIME,
        ),
        SwitchTo(
            text=I18nFormat("btn-promocode.activations"),
            id="promo_activations",
            state=DashboardPromocodes.ACTIVATIONS,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocode.subscription-plan"),
            id="promo_plan_pick",
            state=DashboardPromocodes.PLAN_PICK,
            when=F["promocode_type"] == PromocodeRewardType.SUBSCRIPTION,
        ),
    ),
    Row(
        Button(
            text=I18nFormat("btn-promocode.confirm"),
            id="promo_confirm",
            on_click=on_confirm_promocode,
            style=Style(ButtonStyle.SUCCESS),
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocodes-delete"),
            id="promo_to_delete",
            state=DashboardPromocodes.DELETE_CONFIRM,
            when=F["promocode_has_id"],
        ),
    ),
    Row(
        Start(
            text=I18nFormat("btn-back.general"),
            id="promo_back_main",
            state=DashboardPromocodes.MAIN,
            mode=StartMode.RESET_STACK,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.CONFIGURATOR,
    getter=configurator_getter,
)

promocode_delete_confirm = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-delete-confirm"),
    Row(
        Button(
            text=I18nFormat("btn-promocode.delete-yes"),
            id="promo_delete_yes",
            on_click=on_promocode_delete_confirmed,
            style=Style(ButtonStyle.DANGER),
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back.general"),
            id="promo_delete_back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.DELETE_CONFIRM,
    getter=promocode_delete_confirm_getter,
)

promocodes_list = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocodes-list"),
    ScrollingGroup(
        Select(
            text=Format("{item[code]} ({item[rtype]})"),
            id="promo_list_select",
            item_id_getter=lambda item: item["id"],
            items="promocodes",
            type_factory=int,
            on_click=on_promocode_select,
        ),
        id="promo_list_scroll",
        width=1,
        height=7,
        hide_on_single_page=True,
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back.general"),
            id="promo_list_back",
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
            text=I18nFormat("btn-back.general"),
            id="promo_search_back",
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
            text=Format("{item[code]} ({item[rtype]})"),
            id="promo_search_select",
            item_id_getter=lambda item: item["id"],
            items="search_results",
            type_factory=int,
            on_click=on_promocode_select,
        ),
        id="promo_search_scroll",
        width=1,
        height=7,
        hide_on_single_page=True,
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back.general"),
            id="promo_search_results_back",
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
            text=I18nFormat("btn-back.general"),
            id="promo_code_back",
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
            id="promo_select_reward_type",
            item_id_getter=lambda item: item.value,
            items="reward_types",
            type_factory=PromocodeRewardType,
            on_click=on_promocode_reward_type_select,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back.general"),
            id="promo_type_back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.TYPE,
    getter=promocode_reward_types_getter,
)

promocode_reward = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-reward", promocode_type=F["promocode_type"]),
    I18nFormat("msg-promocode-reward-numeric-hint", when=F["needs_numeric_reward"]),
    I18nFormat("msg-promocode-reward-subscription", when=F["needs_subscription_plan"]),
    Row(
        SwitchTo(
            text=I18nFormat("btn-promocode.subscription-plan"),
            id="promo_reward_pick_plan",
            state=DashboardPromocodes.PLAN_PICK,
            when=F["needs_subscription_plan"],
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back.general"),
            id="promo_reward_back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_promocode_reward_input),
    IgnoreUpdate(),
    state=DashboardPromocodes.REWARD,
    getter=promocode_reward_getter,
)

promocode_plan_pick = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-plan-pick"),
    ScrollingGroup(
        Select(
            text=Format("{item[name]}"),
            id="promo_pick_plan",
            item_id_getter=lambda item: item["id"],
            items="promocode_plans",
            type_factory=int,
            on_click=on_promocode_reward_plan_select,
        ),
        id="promo_plans_scroll",
        width=1,
        height=8,
        hide_on_single_page=True,
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back.general"),
            id="promo_plan_pick_back",
            state=DashboardPromocodes.REWARD,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.PLAN_PICK,
    getter=promocode_plan_pick_getter,
)

promocode_plan_duration = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-plan-duration", plan_name=F["plan_name"]),
    I18nFormat("msg-promocode-plan-duration-missing", when=~F["has_plan_durations"]),
    Column(
        Select(
            text=Format("⌛ {item[caption]}"),
            id="promo_pick_duration",
            item_id_getter=lambda item: item["days"],
            items="plan_durations",
            type_factory=int,
            on_click=on_promocode_reward_duration_select,
        ),
        when=F["has_plan_durations"],
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back.general"),
            id="promo_plan_dur_back",
            state=DashboardPromocodes.PLAN_PICK,
        ),
    ),
    IgnoreUpdate(),
    state=DashboardPromocodes.PLAN_DURATION,
    getter=promocode_plan_duration_getter,
)

promocode_lifetime = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-promocode-lifetime"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back.general"),
            id="promo_lifetime_back",
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
            text=I18nFormat("btn-back.general"),
            id="promo_act_back",
            state=DashboardPromocodes.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_promocode_max_activations_input),
    IgnoreUpdate(),
    state=DashboardPromocodes.ACTIVATIONS,
)

router = Dialog(
    promocodes_main,
    promocodes_list,
    promocodes_search,
    promocodes_search_results,
    configurator,
    promocode_delete_confirm,
    promocode_code,
    promocode_type,
    promocode_reward,
    promocode_plan_pick,
    promocode_plan_duration,
    promocode_lifetime,
    promocode_activations,
)
