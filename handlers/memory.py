"""
Хендлер для управления долгосрочной памятью агентов.
Просмотр, удаление фактов.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from db.memory import get_all_user_memories, delete_memory, clear_all_memory, clear_agent_memory
from db.agents import get_agent

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "menu:memory")
async def on_memory_menu(callback: CallbackQuery):
    """Показывает сохранённые факты."""
    uid = callback.from_user.id
    memories = get_all_user_memories(uid, limit=30)

    if not memories:
        text = (
            "🧠 **Память агентов**\n\n"
            "Пока ничего не запомнено.\n"
            "Агенты автоматически запоминают ключевые факты "
            "из ваших диалогов для будущих сессий."
        )
        buttons = [[InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")]]
    else:
        text = "🧠 **Память агентов**\n\n"
        # Группируем по агентам
        by_agent = {}
        for m in memories:
            aid = m["agent_id"]
            if aid not in by_agent:
                by_agent[aid] = []
            by_agent[aid].append(m)

        for aid, facts in by_agent.items():
            agent = get_agent(aid)
            name = f"{agent['emoji']} {agent['name']}" if agent else f"Агент #{aid}"
            text += f"**{name}:**\n"
            for f in facts[:5]:
                text += f"  • [{f['category']}] {f['fact'][:80]}\n"
            if len(facts) > 5:
                text += f"  ... и ещё {len(facts) - 5}\n"
            text += "\n"

        buttons = [
            [InlineKeyboardButton(text="🗑 Очистить всю память", callback_data="memory:clear_all")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
        ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "memory:clear_all")
async def on_memory_clear(callback: CallbackQuery):
    """Очищает всю память."""
    uid = callback.from_user.id
    clear_all_memory(uid)

    await callback.answer("🗑 Вся память очищена", show_alert=True)
    await on_memory_menu(callback)
