from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from app.config import settings
from app.models import MealType


def get_user_tz() -> ZoneInfo: return ZoneInfo(settings.user_timezone)


def to_user_tz(dt: datetime) -> datetime: return dt.astimezone(get_user_tz())


def detect_meal_type(dt: datetime) -> MealType:
    hour = to_user_tz(dt).hour
    if 9 <= hour <= 11: return MealType.BREAKFAST
    if 12 <= hour <= 15: return MealType.LUNCH
    if 17 <= hour <= 21: return MealType.DINNER
    return MealType.SNACK


def yazio_daytime(meal_type: str) -> str:
    return {"breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner", "snack": "snacks"}.get(meal_type, "snacks")


def format_meal_card(meal: dict) -> str:
    emoji = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙", "snack": "🍿"}.get(meal["meal_type"], "🍽️")
    sync = "✅ <b>Synced to Yazio</b>" if meal.get("yazio_synced_at") else "⚠️ <b>Not synced</b>"
    err = f"\n<i>{escape(meal['yazio_last_error'])}</i>" if meal.get("yazio_last_error") else ""
    return (
        f"{emoji} <b>{meal['meal_type'].capitalize()}</b> • {to_user_tz(meal['consumed_at']).strftime('%H:%M')}\n"
        f"<b>{escape(meal['description'])}</b>\n\n"
        f"🔥 C: <b>{meal['calories']:.0f}</b> | 🥩 P: <b>{meal['protein']:.1f}</b> | 🧈 F: <b>{meal['fat']:.1f}</b> | 🍚 C: <b>{meal['carbs']:.1f}</b>\n\n"
        f"{sync}{err}"
    )


def format_copy_view(meal: dict) -> str:
    return f"<b>Copy this to Yazio AI:</b>\n\n<code>{escape(meal['description'])}, {meal['calories']:.0f} kcal, P {meal['protein']:.1f}g, F {meal['fat']:.1f}g, C {meal['carbs']:.1f}g</code>"


def format_daily_summary(meals: list[dict], totals: dict, now_utc: datetime) -> str:
    date_str = to_user_tz(now_utc).strftime("%Y-%m-%d")
    if not meals: return f"📊 <b>Today — {date_str}</b>\n\nNo meals logged yet."
    lines = [f"📊 <b>Today — {date_str}</b>\n"]
    for m in meals:
        emoji = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙", "snack": "🍿"}.get(m["meal_type"], "🍽️")
        lines.append(
            f"{emoji} {to_user_tz(m['consumed_at']).strftime('%H:%M')} — <b>{escape(m['description'])}</b> ({m['calories']:.0f} kcal) {'✅' if m.get('yazio_synced_at') else '⚠️'}")
    lines.extend(["", f"🔥 Total: <b>{totals['calories']:.0f}</b> kcal",
                  f"🥩 P: <b>{totals['protein']:.1f}</b>g | 🧈 F: <b>{totals['fat']:.1f}</b>g | 🍚 C: <b>{totals['carbs']:.1f}</b>g"])
    return "\n".join(lines)
