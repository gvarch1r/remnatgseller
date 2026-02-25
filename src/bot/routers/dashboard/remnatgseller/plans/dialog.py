from uuid import UUID

from aiogram_dialog import Dialog, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Column,
    CopyText,
    ListGroup,
    Row,
    Select,
    Start,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Format
from magic_filter import F
from remnapy.enums.users import TrafficLimitStrategy

from src.bot.keyboards import main_menu_button
from src.bot.states import DashboardRemnatgseller, RemnatgsellerPlans
from src.bot.widgets import Banner, I18nFormat, IgnoreUpdate
from src.core.enums import BannerName, Currency, PlanAvailability, PlanType

from .getters import (
    allowed_users_getter,
    availability_getter,
    configurator_getter,
    description_getter,
    durations_getter,
    external_squads_getter,
    internal_squads_getter,
    name_getter,
    plans_getter,
    price_getter,
    prices_getter,
    squads_getter,
    tag_getter,
    traffic_getter,
    type_getter,
)
from .handlers import (
    on_active_toggle,
    on_allowed_user_input,
    on_allowed_user_remove,
    on_availability_select,
    on_confirm_plan,
    on_currency_select,
    on_description_delete,
    on_description_input,
    on_devices_input,
    on_duration_input,
    on_duration_remove,
    on_duration_select,
    on_external_squad_select,
    on_internal_squad_select,
    on_name_input,
    on_plan_delete,
    on_plan_move,
    on_plan_select,
    on_price_input,
    on_squads,
    on_strategy_select,
    on_tag_delete,
    on_tag_input,
    on_traffic_input,
    on_type_select,
)

plans = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plans-main"),
    Row(
        SwitchTo(
            I18nFormat("btn-plans-create"),
            id="create",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    ListGroup(
        Row(
            Button(
                text=I18nFormat(
                    "btn-plan",
                    name=F["item"]["name"],
                    is_active=F["item"]["is_active"],
                ),
                id="select_plan",
                on_click=on_plan_select,
            ),
            Button(
                text=Format("🔼"),
                id="move_plan",
                on_click=on_plan_move,
            ),
        ),
        id="plans_list",
        item_id_getter=lambda item: item["id"],
        items="plans",
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
    state=RemnatgsellerPlans.MAIN,
    getter=plans_getter,
)

configurator = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-configurator"),
    Row(
        Button(
            text=I18nFormat("btn-plan-active", is_active=F["is_active"]),
            id="active_toggle",
            on_click=on_active_toggle,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-plan-name"),
            id="name",
            state=RemnatgsellerPlans.NAME,
        ),
        SwitchTo(
            text=I18nFormat("btn-plan-description"),
            id="description",
            state=RemnatgsellerPlans.DESCRIPTION,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-plan-availability"),
            id="availability",
            state=RemnatgsellerPlans.AVAILABILITY,
        ),
        SwitchTo(
            text=I18nFormat("btn-plan-type"),
            id="type",
            state=RemnatgsellerPlans.TYPE,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-plan-traffic"),
            id="traffic",
            state=RemnatgsellerPlans.TRAFFIC,
            when=~F["is_unlimited_traffic"],
        ),
        SwitchTo(
            text=I18nFormat("btn-plan-devices"),
            id="devices",
            state=RemnatgsellerPlans.DEVICES,
            when=~F["is_unlimited_devices"],
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-plan-tag"),
            id="tag",
            state=RemnatgsellerPlans.TAG,
        ),
        Button(
            text=I18nFormat("btn-plan-squads"),
            id="squads",
            on_click=on_squads,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-plan-allowed"),
            id="allowed",
            state=RemnatgsellerPlans.ALLOWED,
            when=F["availability"] == PlanAvailability.ALLOWED,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-plan-durations-prices"),
            id="durations_prices",
            state=RemnatgsellerPlans.DURATIONS,
        ),
    ),
    Row(
        Button(
            text=I18nFormat("btn-plan-create"),
            id="create",
            on_click=on_confirm_plan,
        ),
        when=~F["is_edit"],
    ),
    Row(
        Button(
            text=I18nFormat("btn-plan-save"),
            id="save",
            on_click=on_confirm_plan,
        ),
        Button(
            text=I18nFormat("btn-plan-delete"),
            id="delete_plan",
            on_click=on_plan_delete,
        ),
        when=F["is_edit"],
    ),
    Row(
        Start(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.MAIN,
            mode=StartMode.RESET_STACK,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.CONFIGURATOR,
    getter=configurator_getter,
)

plan_name = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-name"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_name_input),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.NAME,
    getter=name_getter,
)

plan_description = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-description"),
    Row(
        Button(
            text=I18nFormat("btn-plan-description-remove"),
            id="remove",
            on_click=on_description_delete,
        ),
        when=F["description"],
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_description_input),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.DESCRIPTION,
    getter=description_getter,
)

plan_tag = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-tag"),
    Row(
        Button(
            text=I18nFormat("btn-plan-tag-remove"),
            id="remove",
            on_click=on_tag_delete,
        ),
        when=F["tag"],
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_tag_input),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.TAG,
    getter=tag_getter,
)

plan_type = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-type"),
    Column(
        Select(
            text=I18nFormat("btn-plan-type-choice", type=F["item"]),
            id="select_type",
            item_id_getter=lambda item: item.value,
            items="types",
            type_factory=PlanType,
            on_click=on_type_select,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.TYPE,
    getter=type_getter,
)

plan_availability = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-availability"),
    Column(
        Select(
            text=I18nFormat("btn-plan-availability-choice", type=F["item"]),
            id="select_availability",
            item_id_getter=lambda item: item.value,
            items="availability",
            type_factory=PlanAvailability,
            on_click=on_availability_select,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.AVAILABILITY,
    getter=availability_getter,
)

plan_traffic = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-traffic"),
    Column(
        Select(
            text=I18nFormat(
                "btn-plan-traffic-strategy-choice",
                strategy_type=F["item"]["strategy"],
                selected=F["item"]["selected"],
            ),
            id="select_strategy",
            item_id_getter=lambda item: item["strategy"].value,
            items="strategys",
            type_factory=TrafficLimitStrategy,
            on_click=on_strategy_select,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_traffic_input),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.TRAFFIC,
    getter=traffic_getter,
)

plan_devices = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-devices"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_devices_input),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.DEVICES,
)

plan_durations = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-durations"),
    ListGroup(
        Row(
            Button(
                text=I18nFormat("btn-plan-duration", value=F["item"]["days"]),
                id="select_duration",
                on_click=on_duration_select,  # type: ignore[arg-type]
            ),
            Button(
                text=Format("❌"),
                id="remove_duration",
                on_click=on_duration_remove,
                when=F["data"]["deletable"],
            ),
        ),
        id="duration_list",
        item_id_getter=lambda item: item["days"],
        items="durations",
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-plan-duration-add"),
            id="duration_add",
            state=RemnatgsellerPlans.DURATION_ADD,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.DURATIONS,
    getter=durations_getter,
)

plan_durations_add = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-duration"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.DURATIONS,
        ),
    ),
    MessageInput(func=on_duration_input),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.DURATION_ADD,
)

plan_prices = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-prices", value=F["duration"]),
    Column(
        Select(
            text=I18nFormat(
                "btn-plan-price-choice",
                price=F["item"]["price"],
                currency=F["item"]["currency"].value,
            ),
            id="select_price",
            item_id_getter=lambda item: item["currency"].value,
            items="prices",
            type_factory=Currency,
            on_click=on_currency_select,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.DURATIONS,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.PRICES,
    getter=prices_getter,
)

plan_price = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-price", value=F["duration"], currency=F["currency"]),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.PRICES,
        ),
    ),
    MessageInput(func=on_price_input),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.PRICE,
    getter=price_getter,
)

plan_allowed_users = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-allowed-users"),
    ListGroup(
        Row(
            CopyText(
                text=Format("{item}"),
                copy_text=Format("{item}"),
            ),
            Button(
                text=Format("❌"),
                id="remove_allowed_user",
                on_click=on_allowed_user_remove,
            ),
        ),
        id="allowed_users_list",
        item_id_getter=lambda item: item,
        items="allowed_users",
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    MessageInput(func=on_allowed_user_input),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.ALLOWED,
    getter=allowed_users_getter,
)

plan_squads = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-squads"),
    Row(
        SwitchTo(
            text=I18nFormat("btn-plan-internal-squads"),
            id="internal",
            state=RemnatgsellerPlans.INTERNAL_SQUADS,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-plan-external-squads"),
            id="external",
            state=RemnatgsellerPlans.EXTERNAL_SQUADS,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.CONFIGURATOR,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.SQUADS,
    getter=squads_getter,
)

plan_internal_squads = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-internal-squads"),
    Column(
        Select(
            text=I18nFormat(
                "btn-squad-choice",
                name=F["item"]["name"],
                selected=F["item"]["selected"],
            ),
            id="select_squad",
            item_id_getter=lambda item: item["uuid"],
            items="squads",
            type_factory=UUID,
            on_click=on_internal_squad_select,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.SQUADS,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.INTERNAL_SQUADS,
    getter=internal_squads_getter,
)

plan_external_squads = Window(
    Banner(BannerName.DASHBOARD),
    I18nFormat("msg-plan-external-squads"),
    Column(
        Select(
            text=I18nFormat(
                "btn-squad-choice",
                name=F["item"]["name"],
                selected=F["item"]["selected"],
            ),
            id="select_squad",
            item_id_getter=lambda item: item["uuid"],
            items="squads",
            type_factory=UUID,
            on_click=on_external_squad_select,
        ),
    ),
    Row(
        SwitchTo(
            text=I18nFormat("btn-back"),
            id="back",
            state=RemnatgsellerPlans.SQUADS,
        ),
    ),
    IgnoreUpdate(),
    state=RemnatgsellerPlans.EXTERNAL_SQUADS,
    getter=external_squads_getter,
)

router = Dialog(
    plans,
    configurator,
    plan_name,
    plan_description,
    plan_tag,
    plan_type,
    plan_availability,
    plan_traffic,
    plan_devices,
    plan_durations,
    plan_durations_add,
    plan_prices,
    plan_price,
    plan_allowed_users,
    plan_squads,
    plan_internal_squads,
    plan_external_squads,
)
