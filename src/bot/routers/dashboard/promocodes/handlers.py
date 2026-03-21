from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from loguru import logger

from src.bot.states import Dashboard, DashboardPromocodes
from src.core.constants import PROMOCODE_PENDING_PLAN_ID, USER_KEY
from src.core.enums import PromocodeAvailability, PromocodeRewardType
from src.core.utils.adapter import DialogDataAdapter
from src.core.utils.formatters import format_user_log as log
from src.core.utils.message_payload import MessagePayload
from src.infrastructure.database.models.dto import PlanSnapshotDto, PromocodeDto, UserDto
from src.services.notification import NotificationService
from src.services.plan import PlanService
from src.services.promocode import PromocodeService


@inject
async def on_active_toggle(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
) -> None:
    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto)

    if promocode is None:
        promocode = PromocodeDto()
        adapter.save(promocode)

    promocode.is_active = not promocode.is_active
    adapter.save(promocode)
    logger.debug(f"Toggled promocode is_active -> {promocode.is_active}")


@inject
async def on_confirm_promocode(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    notification_service: FromDishka[NotificationService],
    promocode_service: FromDishka[PromocodeService],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]

    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto)

    if not promocode:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-save-error"),
        )
        return

    if not promocode.code or not promocode.code.strip():
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-invalid-code"),
        )
        return

    promocode.code = promocode.code.strip().upper()

    if promocode.reward_type == PromocodeRewardType.SUBSCRIPTION and not promocode.plan:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-subscription-plan-required"),
        )
        return

    try:
        if promocode.id:
            existing = await promocode_service.get_by_code(promocode.code)
            if existing and existing.id != promocode.id:
                await notification_service.notify_user(
                    user=user,
                    payload=MessagePayload(i18n_key="ntf-promocode-code-exists"),
                )
                return
            updated = await promocode_service.update(promocode)
            if updated:
                logger.info(f"{log(user)} Updated promocode '{promocode.code}'")
                await notification_service.notify_user(
                    user=user,
                    payload=MessagePayload(i18n_key="ntf-promocode-updated-success"),
                )
        else:
            existing = await promocode_service.get_by_code(promocode.code)
            if existing:
                await notification_service.notify_user(
                    user=user,
                    payload=MessagePayload(i18n_key="ntf-promocode-code-exists"),
                )
                return
            await promocode_service.create(promocode)
            logger.info(f"{log(user)} Created promocode '{promocode.code}'")
            await notification_service.notify_user(
                user=user,
                payload=MessagePayload(i18n_key="ntf-promocode-created-success"),
            )
    except Exception as exception:
        logger.exception(f"{log(user)} Failed to save promocode: {exception}")
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-save-error"),
        )
        return

    await dialog_manager.reset_stack()
    await dialog_manager.start(state=DashboardPromocodes.MAIN)


@inject
async def on_promocode_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    promocode_service: FromDishka[PromocodeService],
    selected_id: str,
) -> None:
    # Select can pass int or str depending on type_factory
    promocode_id = int(selected_id) if isinstance(selected_id, str) else selected_id
    user: UserDto = dialog_manager.middleware_data[USER_KEY]

    promocode = await promocode_service.get(promocode_id)
    if not promocode:
        return

    logger.info(f"{log(user)} Selected promocode '{promocode.code}' for editing")
    adapter = DialogDataAdapter(dialog_manager)
    adapter.save(promocode)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_search(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    promocode_service: FromDishka[PromocodeService],
    notification_service: FromDishka[NotificationService],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]

    if not user.is_privileged:
        return

    query = message.text.strip() if message.text else ""
    if not query:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-search-empty"),
        )
        return

    found = await promocode_service.search_by_code(query)

    if not found:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-not-found"),
        )
    elif len(found) == 1:
        adapter = DialogDataAdapter(dialog_manager)
        adapter.save(found[0])
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
    else:
        dialog_manager.dialog_data["search_results"] = [
            p.model_dump(mode="json") for p in found
        ]
        await dialog_manager.switch_to(state=DashboardPromocodes.SEARCH_RESULTS)


@inject
async def on_promocode_code_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    notification_service: FromDishka[NotificationService],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    text = message.text.strip() if message.text else ""
    if not text:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-invalid-code"),
        )
        return

    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto) or PromocodeDto()
    promocode.code = text.upper()
    adapter.save(promocode)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


async def on_promocode_reward_type_select(
    callback: CallbackQuery,
    widget: Select[PromocodeRewardType],
    dialog_manager: DialogManager,
    selected_type: PromocodeRewardType,
) -> None:
    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto) or PromocodeDto()
    promocode.reward_type = selected_type
    adapter.save(promocode)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


async def on_promocode_availability_select(
    callback: CallbackQuery,
    widget: Select[PromocodeAvailability],
    dialog_manager: DialogManager,
    selected_availability: PromocodeAvailability,
) -> None:
    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto) or PromocodeDto()
    promocode.availability = selected_availability
    adapter.save(promocode)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_reward_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    notification_service: FromDishka[NotificationService],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    raw = message.text.strip() if message.text else ""

    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto) or PromocodeDto()

    if promocode.reward_type == PromocodeRewardType.SUBSCRIPTION:
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    if not raw or not raw.isdigit():
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-reward-invalid-number"),
        )
        return

    value = int(raw)
    rt = promocode.reward_type

    if rt in (PromocodeRewardType.PERSONAL_DISCOUNT, PromocodeRewardType.PURCHASE_DISCOUNT):
        if not 1 <= value <= 100:
            await notification_service.notify_user(
                user=user,
                payload=MessagePayload(i18n_key="ntf-promocode-reward-invalid-percent"),
            )
            return
    elif rt == PromocodeRewardType.DURATION and value < 1:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-reward-invalid-number"),
        )
        return
    elif rt in (PromocodeRewardType.TRAFFIC, PromocodeRewardType.DEVICES) and value < 1:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-reward-invalid-number"),
        )
        return

    promocode.reward = value
    adapter.save(promocode)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_lifetime_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    notification_service: FromDishka[NotificationService],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    raw = message.text.strip() if message.text else ""

    if not raw or not raw.lstrip("-").isdigit():
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-lifetime-invalid"),
        )
        return

    value = int(raw)
    if value < -1:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-lifetime-invalid"),
        )
        return

    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto) or PromocodeDto()
    promocode.lifetime = value
    adapter.save(promocode)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_max_activations_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    notification_service: FromDishka[NotificationService],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    raw = message.text.strip() if message.text else ""

    if not raw or not raw.lstrip("-").isdigit():
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-activations-invalid"),
        )
        return

    value = int(raw)
    if value < -1:
        await notification_service.notify_user(
            user=user,
            payload=MessagePayload(i18n_key="ntf-promocode-activations-invalid"),
        )
        return

    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto) or PromocodeDto()
    promocode.max_activations = value
    adapter.save(promocode)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_reward_plan_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    plan_service: FromDishka[PlanService],
    selected_id: str,
) -> None:
    plan_id = int(selected_id)
    plan = await plan_service.get(plan_id)
    if not plan or not plan.is_active:
        return

    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto) or PromocodeDto()
    if promocode.reward_type != PromocodeRewardType.SUBSCRIPTION:
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    if not plan.durations:
        promocode.plan = PlanSnapshotDto.from_plan(plan, -1)
        adapter.save(promocode)
        dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    if len(plan.durations) == 1:
        promocode.plan = PlanSnapshotDto.from_plan(plan, plan.durations[0].days)
        adapter.save(promocode)
        dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    dialog_manager.dialog_data[PROMOCODE_PENDING_PLAN_ID] = plan_id
    await dialog_manager.switch_to(state=DashboardPromocodes.PLAN_DURATION)


@inject
async def on_promocode_reward_duration_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    plan_service: FromDishka[PlanService],
    selected_id: str,
) -> None:
    days = int(selected_id)
    raw_id = dialog_manager.dialog_data.get(PROMOCODE_PENDING_PLAN_ID)
    if raw_id is None:
        await dialog_manager.switch_to(state=DashboardPromocodes.PLAN_PICK)
        return

    plan = await plan_service.get(int(raw_id))
    if not plan:
        dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
        await dialog_manager.switch_to(state=DashboardPromocodes.PLAN_PICK)
        return

    if not any(d.days == days for d in plan.durations):
        return

    adapter = DialogDataAdapter(dialog_manager)
    promocode = adapter.load(PromocodeDto) or PromocodeDto()
    promocode.plan = PlanSnapshotDto.from_plan(plan, days)
    adapter.save(promocode)
    dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
