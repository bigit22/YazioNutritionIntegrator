import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import router
from app.bot.middleware import AuthMiddleware
from app.config import settings
from app.db import close_db, init_db

logging.basicConfig(level=logging.INFO)


async def main():
    # 1. Подключаемся к базе
    await init_db()

    # 2. Инициализируем бота
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # 3. Подключаем мидлварь и роутеры
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.include_router(router)

    # 4. Удаляем вебхук (чтобы polling работал)
    await bot.delete_webhook(drop_pending_updates=True)

    print("🚀 Бот запущен в режиме polling (локально)!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
