"""
Общие клавиатуры: подтверждение, отмена.
"""

from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def confirm_kb(action: str, target_id: Optional[int] = None) -> InlineKeyboardMarkup:
    suffix = f":{target_id}" if target_id is not None else ""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{action}{suffix}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel:{action}{suffix}"),
        ]
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel:input")],
    ])
