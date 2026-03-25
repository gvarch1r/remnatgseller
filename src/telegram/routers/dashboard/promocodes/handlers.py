from adaptix import Retort
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from loguru import logger

from src.application.common import Notifier, TranslatorRunner
from src.application.common.dao import PlanDao, PromocodeDao
from src.application.common.uow import UnitOfWork
from src.application.dto import MessagePayloadDto, PlanSnapshotDto, PromocodeDto, UserDto
from src.core.constants import PROMOCODE_PENDING_PLAN_ID, USER_KEY
from src.core.enums import PromocodeRewardType
from src.telegram.states import Dashboard, DashboardPromocodes


def _pc_key() -> str:
    return PromocodeDto.__name__


def _load_pc(dm: DialogManager, retort: Retort) -> PromocodeDto | None:
    raw = dm.dialog_data.get(_pc_key())
    return retort.load(raw, PromocodeDto) if raw else None


def _save_pc(dm: DialogManager, retort: Retort, pc: PromocodeDto) -> None:
    dm.dialog_data[_pc_key()] = retort.dump(pc)


@inject
async def on_active_toggle(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
) -> None:
    pc = _load_pc(dialog_manager, retort) or PromocodeDto()
    pc.is_active = not pc.is_active
    _save_pc(dialog_manager, retort, pc)


@inject
async def on_confirm_promocode(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    uow: FromDishka[UnitOfWork],
    promocode_dao: FromDishka[PromocodeDao],
    notifier: FromDishka[Notifier],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    pc = _load_pc(dialog_manager, retort)
    if not pc:
        await notifier.notify_user(user, i18n_key="ntf-promocode.save-error")
        return

    if not pc.code or not pc.code.strip():
        await notifier.notify_user(user, i18n_key="ntf-promocode.invalid-code")
        return

    pc.code = pc.code.strip().upper()

    if pc.reward_type == PromocodeRewardType.SUBSCRIPTION and not pc.plan:
        await notifier.notify_user(user, i18n_key="ntf-promocode.subscription-plan-required")
        return

    try:
        async with uow:
            if pc.id is not None:
                existing = await promocode_dao.get_by_code(pc.code)
                if existing and existing.id != pc.id:
                    await notifier.notify_user(user, i18n_key="ntf-promocode.code-exists")
                    return
                updated = await promocode_dao.update(pc)
                if not updated:
                    await notifier.notify_user(user, i18n_key="ntf-promocode.save-error")
                    return
                logger.info(
                    "ADMIN_AUDIT action=promocode_save actor_telegram_id={} promocode_id={} code={} op=update",
                    user.telegram_id,
                    pc.id,
                    pc.code,
                )
                await notifier.notify_user(user, i18n_key="ntf-promocode.updated-success")
                await uow.commit()
            else:
                existing = await promocode_dao.get_by_code(pc.code)
                if existing:
                    await notifier.notify_user(user, i18n_key="ntf-promocode.code-exists")
                    return
                await promocode_dao.create(pc)
                logger.info(
                    "ADMIN_AUDIT action=promocode_save actor_telegram_id={} code={} op=create",
                    user.telegram_id,
                    pc.code,
                )
                await notifier.notify_user(user, i18n_key="ntf-promocode.created-success")
                await uow.commit()
    except Exception as exc:
        logger.exception(f"{user.log} Failed to save promocode: {exc}")
        await notifier.notify_user(user, i18n_key="ntf-promocode.save-error")
        return

    await dialog_manager.reset_stack()
    await dialog_manager.start(state=DashboardPromocodes.MAIN, mode=StartMode.RESET_STACK)


@inject
async def on_promocode_delete_confirmed(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    uow: FromDishka[UnitOfWork],
    promocode_dao: FromDishka[PromocodeDao],
    notifier: FromDishka[Notifier],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    pc = _load_pc(dialog_manager, retort)
    if not pc or pc.id is None:
        await notifier.notify_user(user, i18n_key="ntf-promocode.delete-failed")
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    try:
        async with uow:
            ok = await promocode_dao.delete(pc.id)
            await uow.commit()
    except Exception as exc:
        logger.exception(f"{user.log} Delete promocode failed: {exc}")
        await notifier.notify_user(user, i18n_key="ntf-promocode.delete-failed")
        return

    if ok:
        logger.info(
            "ADMIN_AUDIT action=promocode_delete actor_telegram_id={} promocode_id={} code={}",
            user.telegram_id,
            pc.id,
            pc.code,
        )
        await notifier.notify_user(
            user,
            payload=MessagePayloadDto(
                i18n_key="ntf-promocode.deleted-success",
                i18n_kwargs={"code": pc.code},
                disable_default_markup=False,
                delete_after=None,
            ),
        )
        await dialog_manager.reset_stack()
        await dialog_manager.start(state=DashboardPromocodes.MAIN, mode=StartMode.RESET_STACK)
    else:
        await notifier.notify_user(user, i18n_key="ntf-promocode.delete-failed")


@inject
async def on_promocode_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    selected_promocode_id: int,
    retort: FromDishka[Retort],
    promocode_dao: FromDishka[PromocodeDao],
) -> None:
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    row = await promocode_dao.get_by_id(selected_promocode_id)
    if not row:
        return
    logger.info(f"{user.log} Opened promocode editor '{row.code}'")
    _save_pc(dialog_manager, retort, row)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_search(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    promocode_dao: FromDishka[PromocodeDao],
    notifier: FromDishka[Notifier],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    query = message.text.strip() if message.text else ""
    if not query:
        await notifier.notify_user(user, i18n_key="ntf-promocode.search-empty")
        return

    found = await promocode_dao.search_by_code(query)
    if not found:
        await notifier.notify_user(user, i18n_key="ntf-promocode.not-found")
        return

    if len(found) == 1:
        _save_pc(dialog_manager, retort, found[0])
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    dialog_manager.dialog_data["promocode_search_results"] = [retort.dump(p) for p in found]
    await dialog_manager.switch_to(state=DashboardPromocodes.SEARCH_RESULTS)


@inject
async def on_promocode_code_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    notifier: FromDishka[Notifier],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    text = message.text.strip() if message.text else ""
    if not text:
        await notifier.notify_user(user, i18n_key="ntf-promocode.invalid-code")
        return
    pc = _load_pc(dialog_manager, retort) or PromocodeDto()
    pc.code = text.upper()
    _save_pc(dialog_manager, retort, pc)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_reward_type_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    selected_type: PromocodeRewardType,
    retort: FromDishka[Retort],
) -> None:
    pc = _load_pc(dialog_manager, retort) or PromocodeDto()
    pc.reward_type = selected_type
    _save_pc(dialog_manager, retort, pc)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_reward_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    notifier: FromDishka[Notifier],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    raw = message.text.strip() if message.text else ""
    pc = _load_pc(dialog_manager, retort) or PromocodeDto()

    if pc.reward_type == PromocodeRewardType.SUBSCRIPTION:
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    if not raw or not raw.isdigit():
        await notifier.notify_user(user, i18n_key="ntf-promocode.reward-invalid-number")
        return

    value = int(raw)
    rt = pc.reward_type
    if rt in (PromocodeRewardType.PERSONAL_DISCOUNT, PromocodeRewardType.PURCHASE_DISCOUNT):
        if not 1 <= value <= 100:
            await notifier.notify_user(user, i18n_key="ntf-promocode.reward-invalid-percent")
            return
    elif rt == PromocodeRewardType.DURATION and value < 1:
        await notifier.notify_user(user, i18n_key="ntf-promocode.reward-invalid-number")
        return
    elif rt == PromocodeRewardType.TRAFFIC and value < 1:
        await notifier.notify_user(user, i18n_key="ntf-promocode.reward-invalid-number")
        return

    pc.reward = value
    _save_pc(dialog_manager, retort, pc)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_lifetime_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    notifier: FromDishka[Notifier],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    raw = message.text.strip() if message.text else ""
    if not raw or not raw.lstrip("-").isdigit():
        await notifier.notify_user(user, i18n_key="ntf-promocode.lifetime-invalid")
        return
    value = int(raw)
    if value < -1:
        await notifier.notify_user(user, i18n_key="ntf-promocode.lifetime-invalid")
        return
    pc = _load_pc(dialog_manager, retort) or PromocodeDto()
    pc.lifetime = value
    _save_pc(dialog_manager, retort, pc)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_max_activations_input(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
    notifier: FromDishka[Notifier],
) -> None:
    dialog_manager.show_mode = ShowMode.EDIT
    user: UserDto = dialog_manager.middleware_data[USER_KEY]
    raw = message.text.strip() if message.text else ""
    if not raw or not raw.lstrip("-").isdigit():
        await notifier.notify_user(user, i18n_key="ntf-promocode.activations-invalid")
        return
    value = int(raw)
    if value < -1:
        await notifier.notify_user(user, i18n_key="ntf-promocode.activations-invalid")
        return
    pc = _load_pc(dialog_manager, retort) or PromocodeDto()
    pc.max_activations = value
    _save_pc(dialog_manager, retort, pc)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_promocode_reward_plan_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    selected_plan_id: int,
    retort: FromDishka[Retort],
    plan_dao: FromDishka[PlanDao],
) -> None:
    plan = await plan_dao.get_by_id(selected_plan_id)
    if not plan or not plan.is_active:
        return

    pc = _load_pc(dialog_manager, retort) or PromocodeDto()
    if pc.reward_type != PromocodeRewardType.SUBSCRIPTION:
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    if not plan.durations:
        pc.plan = PlanSnapshotDto.from_plan(plan, -1)
        _save_pc(dialog_manager, retort, pc)
        dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    if len(plan.durations) == 1:
        pc.plan = PlanSnapshotDto.from_plan(plan, plan.durations[0].days)
        _save_pc(dialog_manager, retort, pc)
        dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
        await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
        return

    dialog_manager.dialog_data[PROMOCODE_PENDING_PLAN_ID] = selected_plan_id
    await dialog_manager.switch_to(state=DashboardPromocodes.PLAN_DURATION)


@inject
async def on_promocode_reward_duration_select(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    selected_duration: int,
    retort: FromDishka[Retort],
    plan_dao: FromDishka[PlanDao],
) -> None:
    days = selected_duration
    raw_id = dialog_manager.dialog_data.get(PROMOCODE_PENDING_PLAN_ID)
    if raw_id is None:
        await dialog_manager.switch_to(state=DashboardPromocodes.PLAN_PICK)
        return

    plan = await plan_dao.get_by_id(int(raw_id))
    if not plan:
        dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
        await dialog_manager.switch_to(state=DashboardPromocodes.PLAN_PICK)
        return

    if not any(d.days == days for d in plan.durations):
        return

    pc = _load_pc(dialog_manager, retort) or PromocodeDto()
    pc.plan = PlanSnapshotDto.from_plan(plan, days)
    _save_pc(dialog_manager, retort, pc)
    dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)


@inject
async def on_create_promocode_click(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
    retort: FromDishka[Retort],
) -> None:
    dialog_manager.dialog_data.pop(_pc_key(), None)
    dialog_manager.dialog_data.pop(PROMOCODE_PENDING_PLAN_ID, None)
    _save_pc(dialog_manager, retort, PromocodeDto())
    await dialog_manager.switch_to(state=DashboardPromocodes.CONFIGURATOR)
