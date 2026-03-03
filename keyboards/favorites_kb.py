"""
Клавиатуры для избранных агентов.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def favorites_list_kb(agents: list[dict]) -> InlineKeyboardMarkup:
    """Список избранных агентов."""
    buttons = []
    for a in agents:
        buttons.append([
            InlineKeyboardButton(
                text=f"⭐ {a['emoji']} {a['name']}",
                callback_data=f"agent:select:{a['id']}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def favorite_toggle_btn(agent_id: int, is_fav: bool) -> InlineKeyboardButton:
    """Кнопка добавить/убрать из избранного."""
    if is_fav:
        return InlineKeyboardButton(
            text="⭐ Убрать из избранного",
            callback_data=f"fav:remove:{agent_id}",
        )
    return InlineKeyboardButton(
        text="☆ В избранное",
        callback_data=f"fav:add:{agent_id}",
    )
