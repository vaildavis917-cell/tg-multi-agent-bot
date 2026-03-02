"""
Хендлеры выбора агента и взаимодействия с ним.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from db.agents import get_agents, get_agent
from db.state import set_user_state
from db.history import clear_history
from keyboards import agents_list_kb, agent_selected_kb

router = Router()


@router.message(Command("agents"))
async def cmd_agents(message: Message, **kwargs):
    agents = get_agents(active_only=True)
    if not agents:
        await message.answer("😔 Пока нет доступных агентов.")
        return
    await message.answer("🤖 **Выберите агента:**", parse_mode="Markdown", reply_markup=agents_list_kb(agents))


@router.callback_query(F.data == "menu:agents")
async def cb_agents_list(callback: CallbackQuery, **kwargs):
    agents = get_agents(active_only=True)
    if not agents:
        await callback.message.edit_text("😔 Пока нет доступных агентов.")
        await callback.answer()
        return
    await callback.message.edit_text("🤖 **Выберите агента:**", parse_mode="Markdown", reply_markup=agents_list_kb(agents))
    await callback.answer()


@router.callback_query(F.data.startswith("agent:select:"))
async def cb_agent_select(callback: CallbackQuery, **kwargs):
    agent_id = int(callback.data.split(":")[2])
    agent = get_agent(agent_id)
    if not agent:
        await callback.answer("❌ Агент не найден", show_alert=True)
        return
    set_user_state(callback.from_user.id, "agent", agent_id)
    await callback.message.edit_text(
        f"{agent['emoji']} **Агент: {agent['name']}**\n\n"
        f"_{agent['description']}_\n\n"
        "Отправьте сообщение для начала диалога.",
        parse_mode="Markdown",
        reply_markup=agent_selected_kb(agent_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("agent:clear:"))
async def cb_agent_clear(callback: CallbackQuery, **kwargs):
    agent_id = int(callback.data.split(":")[2])
    clear_history(callback.from_user.id, agent_id)
    agent = get_agent(agent_id)
    name = agent["name"] if agent else "Агент"
    await callback.message.edit_text(
        f"🔄 Диалог с **{name}** сброшен. Можете начать заново.",
        parse_mode="Markdown",
        reply_markup=agent_selected_kb(agent_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("agent:info:"))
async def cb_agent_info(callback: CallbackQuery, **kwargs):
    agent_id = int(callback.data.split(":")[2])
    agent = get_agent(agent_id)
    if not agent:
        await callback.answer("❌ Агент не найден", show_alert=True)
        return
    status = "✅ Активен" if agent["is_active"] else "❌ Неактивен"
    await callback.message.edit_text(
        f"{agent['emoji']} **{agent['name']}**\n\n"
        f"📝 {agent['description']}\n"
        f"🆔 ID: `{agent['id']}`\n"
        f"📊 Статус: {status}",
        parse_mode="Markdown",
        reply_markup=agent_selected_kb(agent_id),
    )
    await callback.answer()
