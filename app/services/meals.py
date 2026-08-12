from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from app.config import settings
from app.models import MealType


def get_user_tz() -> ZoneInfo:
    return ZoneInfo(settings.user_timezone)


def to_user_tz(dt: datetime) -> datetime:
    return dt.astimezone(get_user_tz())


def detect_meal_type(dt: datetime) -> MealType:
    hour = to_user_tz(dt).hour
    if 9 <= hour <= 11:
        return MealType.BREAKFAST
    if 12 <= hour <= 15:
        return MealType.LUNCH
    if 17 <= hour <= 21:
        return MealType.DINNER
    return MealType.SNACK


def yazio_daytime(meal_type: str) -> str:
    return {
        "breakfast": "breakfast",
        "lunch": "lunch",
        "dinner": "dinner",
        "snack": "snacks",
    }.get(meal_type, "snacks")


def format_meal_card(meal: dict) -> str:
    emoji = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙", "snack": "🍿"}.get(
        meal["meal_type"], "🍽️"
    )
    sync = (
        "✅ <b>Synced to Yazio</b>"
        if meal.get("yazio_synced_at")
        else "⚠️ <b>Not synced</b>"
    )
    err = (
        f"\n<i>{escape(meal['yazio_last_error'])}</i>"
        if meal.get("yazio_last_error")
        else ""
    )

    portion = ""
    if meal.get("portion_grams"):
        portion = f" • ~{meal['portion_grams']:.0f} g"

    items_block = ""
    if meal.get("items"):
        items_lines = "\n".join(f"  • {escape(item)}" for item in meal["items"])
        items_block = f"\n\n<b>Items:</b>\n{items_lines}"

    return (
        f"{emoji} <b>{meal['meal_type'].capitalize()}</b> • "
        f"{to_user_tz(meal['consumed_at']).strftime('%H:%M')}\n"
        f"<b>{escape(meal['description'])}</b>{portion}"
        f"{items_block}\n\n"
        f"🔥 Calories: <b>{meal['calories']:.0f}</b> kcal\n"
        f"🥩 Protein: <b>{meal['protein']:.1f}</b> g\n"
        f"🧈 Fat: <b>{meal['fat']:.1f}</b> g\n"
        f"🍚 Carbs: <b>{meal['carbs']:.1f}</b> g\n\n"
        f"{sync}{err}"
    )


def format_copy_view(meal: dict) -> str:
    return (
        "<b>Copy this to Yazio AI:</b>\n\n"
        f"<code>{escape(meal['description'])}, {meal['calories']:.0f} kcal, "
        f"P {meal['protein']:.1f}g, F {meal['fat']:.1f}g, C {meal['carbs']:.1f}g</code>"
    )


def format_daily_summary(meals: list[dict], totals: dict, now_utc: datetime) -> str:
    date_str = to_user_tz(now_utc).strftime("%Y-%m-%d")
    if not meals:
        return f"📊 <b>Today — {date_str}</b>\n\nNo meals logged yet."

    lines = [f"📊 <b>Today — {date_str}</b>\n"]
    for m in meals:
        emoji = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙", "snack": "🍿"}.get(
            m["meal_type"], "🍽️"
        )
        sync = "✅" if m.get("yazio_synced_at") else "⚠️"
        lines.append(
            f"{emoji} {to_user_tz(m['consumed_at']).strftime('%H:%M')} — "
            f"<b>{escape(m['description'])}</b> ({m['calories']:.0f} kcal) {sync}"
        )
    lines.append("")
    lines.append(f"🔥 Total Calories: <b>{totals['calories']:.0f}</b> kcal")
    lines.append(f"🥩 Protein: <b>{totals['protein']:.1f}</b> g")
    lines.append(f"🧈 Fat: <b>{totals['fat']:.1f}</b> g")
    lines.append(f"🍚 Carbs: <b>{totals['carbs']:.1f}</b> g")
    return "\n".join(lines)


def format_meal_card_delete_confirm(meal: dict) -> str:
    """Meal card with a delete confirmation question at the bottom."""
    base = format_meal_card(meal)
    return f"{base}\n\n⚠️ <b>Delete this meal?</b>"
