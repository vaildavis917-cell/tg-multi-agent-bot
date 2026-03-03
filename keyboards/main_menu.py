"""
Клавиатура главного меню.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Выбрать агента", callback_data="menu:agents")],
        [InlineKeyboardButton(text="⭐ Избранные агенты", callback_data="menu:favorites")],
        [InlineKeyboardButton(text="💬 Свободный чат с LLM", callback_data="menu:free_chat")],
        [
            InlineKeyboardButton(text="🤝 Мульти-агент", callback_data="menu:multi_agent"),
            InlineKeyboardButton(text="⚖️ Сравнение", callback_data="menu:compare"),
        ],
        [
            InlineKeyboardButton(text="📊 Рынки", callback_data="menu:market"),
            InlineKeyboardButton(text="📈 Графики", callback_data="menu:charts"),
        ],
        [
            InlineKeyboardButton(text="📚 База знаний", callback_data="menu:knowledge"),
            InlineKeyboardButton(text="🧠 Память", callback_data="menu:memory"),
        ],
        [InlineKeyboardButton(text="📋 Отчёты по расписанию", callback_data="menu:scheduled")],
        [InlineKeyboardButton(text="🔄 Сбросить историю", callback_data="menu:clear_history")],
        [
            InlineKeyboardButton(text="🌐 Язык", callback_data="menu:settings"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu:help"),
        ],
    ])


def main_menu_kb_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Выбрать агента", callback_data="menu:agents")],
        [InlineKeyboardButton(text="⭐ Избранные агенты", callback_data="menu:favorites")],
        [InlineKeyboardButton(text="💬 Свободный чат с LLM", callback_data="menu:free_chat")],
        [
            InlineKeyboardButton(text="🤝 Мульти-агент", callback_data="menu:multi_agent"),
            InlineKeyboardButton(text="⚖️ Сравнение", callback_data="menu:compare"),
        ],
        [
            InlineKeyboardButton(text="📊 Рынки", callback_data="menu:market"),
            InlineKeyboardButton(text="📈 Графики", callback_data="menu:charts"),
        ],
        [
            InlineKeyboardButton(text="📚 База знаний", callback_data="menu:knowledge"),
            InlineKeyboardButton(text="🧠 Память", callback_data="menu:memory"),
        ],
        [InlineKeyboardButton(text="📋 Отчёты по расписанию", callback_data="menu:scheduled")],
        [InlineKeyboardButton(text="🔄 Сбросить историю", callback_data="menu:clear_history")],
        [
            InlineKeyboardButton(text="🌐 Язык", callback_data="menu:settings"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu:help"),
        ],
        [InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin:panel")],
    ])


def get_menu_kb(user_id: int) -> InlineKeyboardMarkup:
    """Возвращает нужную клавиатуру в зависимости от роли."""
    return main_menu_kb_admin() if user_id in ADMIN_IDS else main_menu_kb()
