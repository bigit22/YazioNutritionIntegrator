from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from app.config import settings


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id
        if user_id not in settings.allowed_user_ids:
            return None
        return await handler(event, data)
