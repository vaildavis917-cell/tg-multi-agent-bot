"""
Хендлер входа в админ-панель.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import ADMIN_IDS
from keyboards import admin_panel_kb

router = Router()


@router.callback_query(F.data == "admin:panel")
async def cb_admin_panel(callback: CallbackQuery, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Только для администраторов", show_alert=True)
        return
    await callback.message.edit_text(
        "⚙️ **Админ-панель**\n\nВыберите раздел:",
        parse_mode="Markdown",
        reply_markup=admin_panel_kb(),
    )
    await callback.answer()
