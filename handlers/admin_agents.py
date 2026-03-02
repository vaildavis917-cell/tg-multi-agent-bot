"""
Админ-панель: управление AI-агентами (CRUD).
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from db.agents import get_agents, get_agent, add_agent, update_agent, delete_agent
from keyboards import admin_agents_kb, admin_agent_edit_kb, admin_panel_kb, cancel_kb

logger = logging.getLogger(__name__)
router = Router()


# ── FSM-состояния ────────────────────────────────────────

class AgentAdd(StatesGroup):
    waiting_name = State()
    waiting_emoji = State()
    waiting_description = State()
    waiting_prompt = State()


class AgentEdit(StatesGroup):
    waiting_value = State()


# ── Список агентов ───────────────────────────────────────

@router.callback_query(F.data == "admin:agents")
async def cb_agents_list(callback: CallbackQuery, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    agents = get_agents(active_only=False)
    await callback.message.edit_text(
        "🤖 **Управление агентами**",
        parse_mode="Markdown",
        reply_markup=admin_agents_kb(agents),
    )
    await callback.answer()


# ── Добавление агента (пошаговый wizard) ─────────────────

@router.callback_query(F.data == "admin:ag:add")
async def cb_ag_add_start(callback: CallbackQuery, state: FSMContext, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    await state.set_state(AgentAdd.waiting_name)
    await callback.message.edit_text(
        "➕ **Новый агент — шаг 1/4**\n\nВведите **имя** агента:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(AgentAdd.waiting_name)
async def on_ag_name(message: Message, state: FSMContext, **kwargs):
    await state.update_data(name=message.text.strip())
    await state.set_state(AgentAdd.waiting_emoji)
    await message.answer(
        "➕ **Шаг 2/4**\n\nОтправьте **эмодзи** для агента (один символ):",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )


@router.message(AgentAdd.waiting_emoji)
async def on_ag_emoji(message: Message, state: FSMContext, **kwargs):
    await state.update_data(emoji=message.text.strip()[:4])
    await state.set_state(AgentAdd.waiting_description)
    await message.answer(
        "➕ **Шаг 3/4**\n\nВведите **описание** агента (что он делает):",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )


@router.message(AgentAdd.waiting_description)
async def on_ag_desc(message: Message, state: FSMContext, **kwargs):
    await state.update_data(description=message.text.strip())
    await state.set_state(AgentAdd.waiting_prompt)
    await message.answer(
        "➕ **Шаг 4/4**\n\nВведите **системный промпт** агента:\n\n"
        "_(Это инструкция, которую AI получит перед диалогом)_",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )


@router.message(AgentAdd.waiting_prompt)
async def on_ag_prompt(message: Message, state: FSMContext, **kwargs):
    data = await state.get_data()
    await state.clear()
    agent_id = add_agent(
        name=data["name"],
        emoji=data["emoji"],
        description=data["description"],
        system_prompt=message.text.strip(),
    )
    agents = get_agents(active_only=False)
    await message.answer(
        f"✅ Агент **{data['name']}** создан (ID: {agent_id})!",
        parse_mode="Markdown",
        reply_markup=admin_agents_kb(agents),
    )


# ── Редактирование агента ────────────────────────────────

@router.callback_query(F.data.startswith("admin:ag:edit:"))
async def cb_ag_edit(callback: CallbackQuery, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    agent_id = int(callback.data.split(":")[3])
    agent = get_agent(agent_id)
    if not agent:
        await callback.answer("❌ Агент не найден", show_alert=True)
        return
    status = "✅ Активен" if agent["is_active"] else "❌ Неактивен"
    prompt_preview = (agent["system_prompt"][:200] + "...") if len(agent["system_prompt"]) > 200 else agent["system_prompt"]
    await callback.message.edit_text(
        f"{agent['emoji']} **{agent['name']}**\n\n"
        f"📝 {agent['description']}\n"
        f"📊 {status}\n\n"
        f"🧠 Промпт:\n`{prompt_preview}`",
        parse_mode="Markdown",
        reply_markup=admin_agent_edit_kb(agent_id, bool(agent["is_active"])),
    )
    await callback.answer()


# ── Изменение отдельных полей ────────────────────────────

@router.callback_query(F.data.startswith("admin:ag:set_"))
async def cb_ag_set_field(callback: CallbackQuery, state: FSMContext, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    parts = callback.data.split(":")
    # admin:ag:set_name:123 → field = "name", agent_id = 123
    field = parts[2].replace("set_", "")  # name, emoji, desc, prompt
    agent_id = int(parts[3])

    field_map = {
        "name": ("имя", "name"),
        "emoji": ("эмодзи", "emoji"),
        "desc": ("описание", "description"),
        "prompt": ("системный промпт", "system_prompt"),
    }

    label, db_field = field_map.get(field, ("значение", field))
    await state.set_state(AgentEdit.waiting_value)
    await state.update_data(agent_id=agent_id, db_field=db_field)
    await callback.message.edit_text(
        f"✏️ Введите новое **{label}** для агента:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(AgentEdit.waiting_value)
async def on_ag_edit_value(message: Message, state: FSMContext, **kwargs):
    data = await state.get_data()
    await state.clear()
    agent_id = data["agent_id"]
    db_field = data["db_field"]
    update_agent(agent_id, **{db_field: message.text.strip()})
    agent = get_agent(agent_id)
    if agent:
        await message.answer(
            f"✅ Поле обновлено для агента **{agent['name']}**.",
            parse_mode="Markdown",
            reply_markup=admin_agent_edit_kb(agent_id, bool(agent["is_active"])),
        )
    else:
        await message.answer("⚠️ Агент не найден.")


# ── Переключение активности ──────────────────────────────

@router.callback_query(F.data.startswith("admin:ag:toggle:"))
async def cb_ag_toggle(callback: CallbackQuery, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    agent_id = int(callback.data.split(":")[3])
    agent = get_agent(agent_id)
    if not agent:
        await callback.answer("❌ Не найден", show_alert=True)
        return
    new_status = 0 if agent["is_active"] else 1
    update_agent(agent_id, is_active=new_status)
    label = "активирован" if new_status else "деактивирован"
    await callback.answer(f"Агент {label}")
    # Обновляем карточку
    agent = get_agent(agent_id)
    await callback.message.edit_reply_markup(
        reply_markup=admin_agent_edit_kb(agent_id, bool(agent["is_active"])),
    )


# ── Удаление агента ──────────────────────────────────────

@router.callback_query(F.data.startswith("admin:ag:delete:"))
async def cb_ag_delete(callback: CallbackQuery, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return
    agent_id = int(callback.data.split(":")[3])
    delete_agent(agent_id)
    agents = get_agents(active_only=False)
    await callback.message.edit_text(
        "🗑 Агент удалён.\n\n🤖 **Управление агентами**",
        parse_mode="Markdown",
        reply_markup=admin_agents_kb(agents),
    )
    await callback.answer()
