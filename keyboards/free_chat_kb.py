"""
Клавиатура режима свободного чата.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def free_chat_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сбросить диалог", callback_data="free:clear")],
        [InlineKeyboardButton(text="📄 Экспорт", callback_data="export:free")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:back")],
    ])
