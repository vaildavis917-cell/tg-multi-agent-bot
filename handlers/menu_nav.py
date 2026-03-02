"""
Хендлеры навигации по inline-меню (callback queries).
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.state import set_user_state
from db.history import clear_history
from keyboards import get_menu_kb

router = Router()


@router.callback_query(F.data == "menu:back")
async def cb_back(callback: CallbackQuery, **kwargs):
    set_user_state(callback.from_user.id, "menu")
    await callback.message.edit_text(
        "📋 **Главное меню:**",
        parse_mode="Markdown",
        reply_markup=get_menu_kb(callback.from_user.id),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery, **kwargs):
    from handlers.start import HELP
    await callback.message.edit_text(
        HELP,
        parse_mode="Markdown",
        reply_markup=get_menu_kb(callback.from_user.id),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:clear_history")
async def cb_clear(callback: CallbackQuery, **kwargs):
    count = clear_history(callback.from_user.id)
    set_user_state(callback.from_user.id, "menu")
    await callback.message.edit_text(
        f"🔄 История очищена ({count} сообщений).\n\n📋 **Главное меню:**",
        parse_mode="Markdown",
        reply_markup=get_menu_kb(callback.from_user.id),
    )
    await callback.answer()
