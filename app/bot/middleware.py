import logging

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import settings
from app.db import UsersRepository

logger = logging.getLogger(__name__)
users_repo = UsersRepository()


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = None
        user_obj = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id
            user_obj = event.from_user

        if user_id is None:
            return None

        is_admin = user_id in settings.admin_user_ids
        data["is_admin"] = is_admin

        if is_admin:
            return await handler(event, data)

        if await users_repo.is_allowed(user_id):
            return await handler(event, data)

        username = user_obj.username if user_obj else None
        logger.warning(f"Access denied for user {user_id} (@{username})")

        if isinstance(event, Message):
            await event.answer(
                "⛔ <b>Access denied</b>\n\n"
                f"Your Telegram ID: <code>{user_id}</code>\n"
                "Ask the admin to grant access."
            )
        elif isinstance(event, CallbackQuery):
            await event.answer("Access denied", show_alert=True)
        return None
