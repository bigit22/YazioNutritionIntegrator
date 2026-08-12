from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from fastapi import FastAPI, Request, Response

from app.bot.handlers import router
from app.bot.middleware import AuthMiddleware
from app.config import settings
from app.db import init_db, close_db

bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())
dp.include_router(router)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await bot.set_webhook(url=settings.webhook_url, secret_token=settings.webhook_secret)
    yield
    await bot.delete_webhook()
    await bot.session.close()
    await close_db()


app = FastAPI(lifespan=lifespan)


@app.post(settings.webhook_path)
async def telegram_webhook(request: Request) -> Response:
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.webhook_secret:
        return Response(status_code=403)
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return Response(status_code=200)
