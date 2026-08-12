import logging

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.config import settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        logger.info(f"Incoming event from user_id={user_id}, allowed={settings.allowed_user_ids}")

        if user_id not in settings.allowed_user_ids:
            logger.warning(f"User {user_id} NOT in allowed list, ignoring")
            return None
        return await handler(event, data)
