from typing import cast

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message
from loguru import logger

from src.bot.states import Notification
from src.core.utils.formatters import format_user_log as log
from src.infrastructure.database.models.dto import UserDto

router = Router(name=__name__)


@router.callback_query(F.data.startswith(Notification.CLOSE.state))
async def on_close_notification(callback: CallbackQuery, bot: Bot, user: UserDto) -> None:
    notification: Message = cast(Message, callback.message)
    notification_id = notification.message_id

    logger.info(f"{log(user)} Closed notification '{notification_id}'")

    try:
        await callback.answer()
    except Exception:
        pass  # query too old / already answered — ignore

    try:
        await notification.delete()
        logger.debug(f"Notification '{notification_id}' for user '{user.telegram_id}' deleted")
    except Exception:
        try:
            await bot.edit_message_reply_markup(
                chat_id=notification.chat.id,
                message_id=notification.message_id,
                reply_markup=None,
            )
        except Exception:
            pass  # message deleted or too old — ignore
