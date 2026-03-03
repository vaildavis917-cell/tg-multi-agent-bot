"""
Клавиатуры шаблонов быстрых запросов.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def templates_list_kb(templates: list[dict], agent_id: int) -> InlineKeyboardMarkup:
    """Список шаблонов для агента."""
    buttons = []
    for t in templates:
        buttons.append([
            InlineKeyboardButton(
                text=f"⚡ {t['title']}",
                callback_data=f"tpl:use:{t['id']}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад к агенту", callback_data=f"agent:select:{agent_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
