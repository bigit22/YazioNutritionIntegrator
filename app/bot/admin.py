from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.db import UsersRepository

router = Router()
users_repo = UsersRepository()


class AdminStates(StatesGroup):
    waiting_for_user_id = State()


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 List users", callback_data="admin:list")],
        [InlineKeyboardButton(text="➕ Add user", callback_data="admin:add")],
        [InlineKeyboardButton(text="❌ Close", callback_data="admin:close")],
    ])


def back_to_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="admin:menu")],
    ])


def users_list_kb(users: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for u in users:
        label = f"🗑 {u['first_name'] or u['username'] or u['telegram_user_id']}"
        rows.append([InlineKeyboardButton(
            text=label, callback_data=f"admin:del:{u['telegram_user_id']}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Back", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _users_list_text(users: list[dict]) -> str:
    if not users:
        return "👥 <b>No users yet</b>\n\nOnly admins have access."
    lines = ["👥 <b>Allowed users</b>\n"]
    for u in users:
        name = escape(u["first_name"] or u["username"] or "unknown")
        note = f" — <i>{escape(u['note'])}</i>" if u.get("note") else ""
        lines.append(f"• <code>{u['telegram_user_id']}</code> — {name}{note}")
    lines.append("\n<i>Tap a user to remove</i>")
    return "\n".join(lines)


@router.message(Command("admin"))
async def cmd_admin(msg: Message, is_admin: bool):
    if not is_admin:
        return
    await msg.answer("🛠 <b>Admin panel</b>", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin:menu")
async def cb_menu(cb: CallbackQuery, is_admin: bool):
    if not is_admin:
        return await cb.answer()
    await cb.message.edit_text("🛠 <b>Admin panel</b>", reply_markup=admin_menu_kb())
    await cb.answer()


@router.callback_query(F.data == "admin:close")
async def cb_close(cb: CallbackQuery, is_admin: bool):
    if not is_admin:
        return await cb.answer()
    await cb.message.delete()
    await cb.answer()


@router.callback_query(F.data == "admin:list")
async def cb_list(cb: CallbackQuery, is_admin: bool):
    if not is_admin:
        return await cb.answer()
    users = await users_repo.list_users()
    kb = users_list_kb(users) if users else back_to_admin_kb()
    await cb.message.edit_text(_users_list_text(users), reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("admin:del:"))
async def cb_del(cb: CallbackQuery, is_admin: bool):
    if not is_admin:
        return await cb.answer()
    user_id = int(cb.data.split(":")[-1])
    await users_repo.remove_user(user_id)
    await cb.answer(f"Removed {user_id}", show_alert=True)
    users = await users_repo.list_users()
    kb = users_list_kb(users) if users else back_to_admin_kb()
    await cb.message.edit_text(_users_list_text(users), reply_markup=kb)


@router.callback_query(F.data == "admin:add")
async def cb_add(cb: CallbackQuery, state: FSMContext, is_admin: bool):
    if not is_admin:
        return await cb.answer()
    await state.set_state(AdminStates.waiting_for_user_id)
    await cb.message.edit_text(
        "➕ <b>Add user</b>\n\n"
        "Send the Telegram ID (number).\n"
        "Optionally add a note after it, e.g.:\n"
        "<code>123456789 my friend Sasha</code>\n\n"
        "Or /cancel",
        reply_markup=back_to_admin_kb(),
    )
    await cb.answer()


@router.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return
    await state.clear()
    await msg.answer("Cancelled.", reply_markup=admin_menu_kb())


@router.message(AdminStates.waiting_for_user_id)
async def process_add_user(msg: Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return
    text = (msg.text or "").strip()
    parts = text.split(maxsplit=1)
    try:
        new_id = int(parts[0])
    except (ValueError, IndexError):
        await msg.answer("❌ Not a valid ID. Try again or /cancel")
        return

    note = parts[1] if len(parts) > 1 else None
    added = await users_repo.add_user(
        telegram_user_id=new_id, added_by=msg.from_user.id, note=note
    )
    await state.clear()

    if added:
        await msg.answer(
            f"✅ User <code>{new_id}</code> added.",
            reply_markup=admin_menu_kb(),
        )
    else:
        await msg.answer(
            f"⚠️ User <code>{new_id}</code> already in list.",
            reply_markup=admin_menu_kb(),
        )
