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


def agent_selected_kb(agent_id: int, is_fav: bool = False) -> InlineKeyboardMarkup:
    fav_text = "⭐ Убрать из избранного" if is_fav else "☆ В избранное"
    fav_data = f"fav:remove:{agent_id}" if is_fav else f"fav:add:{agent_id}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сбросить диалог", callback_data=f"agent:clear:{agent_id}")],
        [InlineKeyboardButton(text="⚡ Быстрые запросы", callback_data=f"agent:templates:{agent_id}")],
        [InlineKeyboardButton(text="📄 Экспорт диалога", callback_data=f"export:agent:{agent_id}")],
        [InlineKeyboardButton(text=fav_text, callback_data=fav_data)],
        [InlineKeyboardButton(text="📋 Об агенте", callback_data=f"agent:info:{agent_id}")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:back")],
    ])
