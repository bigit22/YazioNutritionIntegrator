import io
from datetime import UTC, datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import (
    back_keyboard,
    confirm_delete_keyboard,
    meal_keyboard,
    summary_from_meal_keyboard,
)
from app.db import MealRepository
from app.services.gemini import gemini_service
from app.services.meals import (
    detect_meal_type,
    format_copy_view,
    format_daily_summary,
    format_meal_card,
    format_meal_card_delete_confirm,
    to_user_tz,
    yazio_daytime,
)
from app.services.yazio import yazio_service

router = Router()
repo = MealRepository()


@router.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer("👋 Send me a photo of your food or a text description!")


@router.message(Command("today"))
async def cmd_today(msg: Message):
    """Standalone /today — no back button (nowhere to go back)."""
    text = await _build_summary_text(msg.from_user.id)
    await msg.answer(text)


@router.message(F.photo | F.text)
async def process_meal(msg: Message):
    if msg.text and msg.text.startswith("/"):
        return
    processing = await msg.answer("🔄 Analyzing...")
    try:
        image_bytes = None
        if msg.photo:
            file = await msg.bot.get_file(msg.photo[-1].file_id)
            buf = io.BytesIO()
            await msg.bot.download_file(file.file_path, destination=buf)
            image_bytes = buf.getvalue()

        user_text = msg.caption if msg.photo else msg.text
        consumed_at = msg.date.replace(tzinfo=UTC)
        meal_type = detect_meal_type(consumed_at)

        nutrition = await gemini_service.analyze(user_text=user_text, image_bytes=image_bytes)
        meal = await repo.create_meal(
            telegram_user_id=msg.from_user.id,
            chat_id=msg.chat.id,
            source_message_id=msg.message_id,
            meal_type=meal_type.value,
            user_text=user_text,
            nutrition=nutrition,
            consumed_at=consumed_at,
        )

        try:
            remote_id, payload = await yazio_service.create_consumed_item(
                meal, yazio_daytime(meal["meal_type"])
            )
            await repo.mark_yazio_synced(meal["id"], remote_id, payload)
        except Exception as e:
            await repo.mark_yazio_error(meal["id"], str(e))

        final_meal = await repo.get_meal(meal["id"], msg.from_user.id)
        await processing.edit_text(
            format_meal_card(final_meal), reply_markup=meal_keyboard(final_meal)
        )
    except Exception as e:
        await processing.edit_text(f"❌ Error: {str(e)}")


@router.callback_query(F.data.startswith("meal:"))
async def meal_callbacks(cb: CallbackQuery):
    action, meal_id = cb.data.split(":")[1:]
    meal = await repo.get_meal(meal_id, cb.from_user.id)
    if not meal or meal.get("deleted_at"):
        return await cb.answer("Meal not found")

    if action == "copy":
        await cb.message.edit_text(format_copy_view(meal), reply_markup=back_keyboard(meal_id))
    elif action == "back":
        await cb.message.edit_text(format_meal_card(meal), reply_markup=meal_keyboard(meal))
    elif action == "delete":
        await cb.message.edit_text(
            format_meal_card_delete_confirm(meal),
            reply_markup=confirm_delete_keyboard(meal_id),
        )
    elif action == "confirm_delete":
        if meal.get("yazio_consumed_item_id"):
            try:
                await yazio_service.delete_consumed_item(meal["yazio_consumed_item_id"])
            except Exception:
                return await cb.answer("Failed to delete from Yazio")
        await repo.soft_delete_meal(meal_id)
        await cb.message.edit_text("🗑 <b>Meal deleted</b>")
    elif action == "sync":
        try:
            remote_id, payload = await yazio_service.create_consumed_item(
                meal, yazio_daytime(meal["meal_type"])
            )
            await repo.mark_yazio_synced(meal["id"], remote_id, payload)
            upd_meal = await repo.get_meal(meal_id, cb.from_user.id)
            await cb.message.edit_text(
                format_meal_card(upd_meal), reply_markup=meal_keyboard(upd_meal)
            )
        except Exception as e:
            await cb.answer(f"Sync failed: {e}", show_alert=True)
    elif action == "today":
        text = await _build_summary_text(cb.from_user.id)
        await cb.message.edit_text(text, reply_markup=summary_from_meal_keyboard(meal_id))
    await cb.answer()


async def _build_summary_text(user_id: int) -> str:
    now_utc = datetime.now(UTC)
    local_now = to_user_tz(now_utc)
    start_local = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)

    meals = await repo.list_day_meals(user_id, start_local, end_local)
    totals = await repo.get_day_totals(user_id, start_local, end_local)
    return format_daily_summary(meals, totals, now_utc)
