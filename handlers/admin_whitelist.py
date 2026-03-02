"""
Админ-панель: управление whitelist.
Формат добавления: ID ТЕГ (например: 7415656277 Vlad)
Можно несколько строк или через запятую.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from db.whitelist import add_to_whitelist, remove_from_whitelist, get_whitelist, update_tag, get_whitelist_user
from keyboards import admin_whitelist_kb, admin_whitelist_list_kb, cancel_kb

logger = logging.getLogger(__name__)
router = Router()


# ── FSM-состояния для ввода данных ───────────────────────

class WLAdd(StatesGroup):
    waiting_user_id = State()


class WLRemove(StatesGroup):
    waiting_user_id = State()


class WLEditTag(StatesGroup):
    waiting_tag = State()


# ── Меню whitelist ───────────────────────────────────────

@router.callback_query(F.data == "admin:whitelist")
async def cb_whitelist_menu(callback: CallbackQuery, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "👥 **Whitelist — управление доступом**",
        parse_mode="Markdown",
        reply_markup=admin_whitelist_kb(),
    )
    await callback.answer()


# ── Список ───────────────────────────────────────────────

@router.callback_query(F.data == "admin:wl:list")
async def cb_wl_list(callback: CallbackQuery, **kwargs):
    users = get_whitelist()
    if not users:
        await callback.message.edit_text(
            "👥 Whitelist пуст.",
            reply_markup=admin_whitelist_kb(),
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        f"👥 **Whitelist** ({len(users)} пользователей):",
        parse_mode="Markdown",
        reply_markup=admin_whitelist_list_kb(users),
    )
    await callback.answer()


# ── Добавить ─────────────────────────────────────────────

@router.callback_query(F.data == "admin:wl:add")
async def cb_wl_add_start(callback: CallbackQuery, state: FSMContext, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    await state.set_state(WLAdd.waiting_user_id)
    await callback.message.edit_text(
        "➕ **Добавление в whitelist**\n\n"
        "Формат: `ID Тег`\n"
        "Примеры:\n"
        "• `7415656277 Vlad`\n"
        "• `123456789 Иван Петров`\n"
        "• `111222333` (без тега тоже можно)\n\n"
        "Можно отправить несколько — каждый с новой строки или через запятую.",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


def _parse_id_tag(raw: str) -> tuple[int | None, str]:
    """
    Парсит строку вида '7415656277 Vlad' → (7415656277, 'Vlad')
    Или '7415656277' → (7415656277, '')
    """
    raw = raw.strip()
    if not raw:
        return None, ""
    parts = raw.split(maxsplit=1)
    try:
        uid = int(parts[0])
        tag = parts[1].strip() if len(parts) > 1 else ""
        return uid, tag
    except ValueError:
        return None, raw


@router.message(WLAdd.waiting_user_id)
async def on_wl_add_input(message: Message, state: FSMContext, **kwargs):
    if message.from_user.id not in ADMIN_IDS:
        return

    # Разделяем по строкам и запятым
    text = message.text.replace(",", "\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    added = []
    errors = []

    for line in lines:
        uid, tag = _parse_id_tag(line)
        if uid is not None:
            add_to_whitelist(uid, tag=tag, added_by=message.from_user.id)
            label = f"{uid}" + (f" ({tag})" if tag else "")
            added.append(label)
        else:
            errors.append(tag or line)

    result_lines = []
    if added:
        result_lines.append("✅ Добавлены: " + ", ".join(added))
    if errors:
        result_lines.append("⚠️ Ошибки (не число): " + ", ".join(errors))

    await state.clear()
    await message.answer("\n".join(result_lines), reply_markup=admin_whitelist_kb())


# ── Удалить ──────────────────────────────────────────────

@router.callback_query(F.data == "admin:wl:remove")
async def cb_wl_remove_start(callback: CallbackQuery, state: FSMContext, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    await state.set_state(WLRemove.waiting_user_id)
    await callback.message.edit_text(
        "➖ **Удаление из whitelist**\n\n"
        "Отправьте Telegram User ID пользователя (число).",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(WLRemove.waiting_user_id)
async def on_wl_remove_input(message: Message, state: FSMContext, **kwargs):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Введите корректный числовой ID.", reply_markup=cancel_kb())
        return

    ok = remove_from_whitelist(uid)
    await state.clear()
    if ok:
        await message.answer(f"✅ Пользователь `{uid}` удалён из whitelist.", parse_mode="Markdown", reply_markup=admin_whitelist_kb())
    else:
        await message.answer(f"⚠️ Пользователь `{uid}` не найден в whitelist.", parse_mode="Markdown", reply_markup=admin_whitelist_kb())


# ── Быстрое удаление из списка ──────────────────────────

@router.callback_query(F.data.startswith("admin:wl:del:"))
async def cb_wl_quick_delete(callback: CallbackQuery, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    uid = int(callback.data.split(":")[3])
    remove_from_whitelist(uid)
    # Обновляем список
    users = get_whitelist()
    if not users:
        await callback.message.edit_text("👥 Whitelist пуст.", reply_markup=admin_whitelist_kb())
    else:
        await callback.message.edit_text(
            f"👥 **Whitelist** ({len(users)} пользователей):",
            parse_mode="Markdown",
            reply_markup=admin_whitelist_list_kb(users),
        )
    await callback.answer(f"Удалён: {uid}")


# ── Редактировать тег ────────────────────────────────────

@router.callback_query(F.data.startswith("admin:wl:tag:"))
async def cb_wl_edit_tag(callback: CallbackQuery, state: FSMContext, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    uid = int(callback.data.split(":")[3])
    user = get_whitelist_user(uid)
    current_tag = user.get("tag", "") if user else ""
    await state.set_state(WLEditTag.waiting_tag)
    await state.update_data(edit_uid=uid)
    await callback.message.edit_text(
        f"🏷 **Редактирование тега**\n\n"
        f"Пользователь: `{uid}`\n"
        f"Текущий тег: {current_tag or '(нет)'}\n\n"
        f"Отправьте новый тег (имя/заметку):",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(WLEditTag.waiting_tag)
async def on_wl_edit_tag_input(message: Message, state: FSMContext, **kwargs):
    if message.from_user.id not in ADMIN_IDS:
        return
    data = await state.get_data()
    uid = data.get("edit_uid")
    new_tag = message.text.strip()
    update_tag(uid, new_tag)
    await state.clear()
    await message.answer(
        f"✅ Тег для `{uid}` обновлён: **{new_tag}**",
        parse_mode="Markdown",
        reply_markup=admin_whitelist_kb(),
    )


# ── Инфо о пользователе ─────────────────────────────────

@router.callback_query(F.data.startswith("admin:wl:info:"))
async def cb_wl_user_info(callback: CallbackQuery, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    uid = int(callback.data.split(":")[3])
    user = get_whitelist_user(uid)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    from datetime import datetime
    added_dt = datetime.fromtimestamp(user["added_at"]).strftime("%d.%m.%Y %H:%M") if user["added_at"] else "—"

    text = (
        f"👤 **Пользователь**\n\n"
        f"🆔 ID: `{user['user_id']}`\n"
        f"🏷 Тег: {user['tag'] or '(нет)'}\n"
        f"📅 Добавлен: {added_dt}\n"
        f"👤 Добавил: `{user['added_by']}`"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷 Изменить тег", callback_data=f"admin:wl:tag:{uid}")],
        [InlineKeyboardButton(text="❌ Удалить из whitelist", callback_data=f"admin:wl:del:{uid}")],
        [InlineKeyboardButton(text="◀️ К списку", callback_data="admin:wl:list")],
    ])

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


# ── Отмена ввода ─────────────────────────────────────────

@router.callback_query(F.data == "cancel:input")
async def cb_cancel_input(callback: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    await callback.message.edit_text(
        "👥 **Whitelist — управление доступом**",
        parse_mode="Markdown",
        reply_markup=admin_whitelist_kb(),
    )
    await callback.answer("Отменено")
