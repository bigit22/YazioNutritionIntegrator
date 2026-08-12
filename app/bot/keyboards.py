from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def meal_keyboard(meal: dict) -> InlineKeyboardMarkup:
    rows = []
    if not meal.get("yazio_synced_at"):
        rows.append([InlineKeyboardButton(
            text="📤 Retry Yazio", callback_data=f"meal:sync:{meal['id']}"
        )])
    rows.append([
        InlineKeyboardButton(text="📋 Copy", callback_data=f"meal:copy:{meal['id']}"),
        InlineKeyboardButton(text="🗑 Delete", callback_data=f"meal:delete:{meal['id']}"),
    ])
    rows.append([
        InlineKeyboardButton(text="📊 Today", callback_data=f"meal:today:{meal['id']}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_keyboard(meal_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yes, delete", callback_data=f"meal:confirm_delete:{meal_id}"),
        InlineKeyboardButton(text="❌ Cancel", callback_data=f"meal:back:{meal_id}"),
    ]])


def back_keyboard(meal_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Back", callback_data=f"meal:back:{meal_id}"),
    ]])


def summary_from_meal_keyboard(meal_id: str) -> InlineKeyboardMarkup:
    """Summary shown from within a meal card — has a back button."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Back to meal", callback_data=f"meal:back:{meal_id}"),
    ]])
