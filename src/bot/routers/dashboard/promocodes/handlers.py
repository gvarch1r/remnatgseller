from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject
from loguru import logger

from src.bot.states import Dashboard, DashboardPromocodes
from src.core.constants import USER_KEY
from src.core.utils.adapter import DialogDataAdapter
from src.core.utils.formatters import format_user_log as log
from src.core.utils.message_payload import MessagePayload
from src.infrastructure.database.models.dto import PromocodeDto, UserDto
from src.services.notification import NotificationService
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
    await dialog_manager.dialog().refresh()


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
