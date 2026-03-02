"""
Клавиатуры для выбора и управления агентами (пользовательская сторона).
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def agents_list_kb(agents: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{a['emoji']} {a['name']}",
            callback_data=f"agent:select:{a['id']}",
        )]
        for a in agents
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def agent_selected_kb(agent_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сбросить диалог", callback_data=f"agent:clear:{agent_id}")],
        [InlineKeyboardButton(text="📋 Об агенте", callback_data=f"agent:info:{agent_id}")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:back")],
    ])
