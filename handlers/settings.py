"""
Хендлер настроек пользователя (выбор языка).
"""

import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from db.user_settings import get_user_lang, set_user_lang
from services.i18n import t
from keyboards import get_menu_kb

logger = logging.getLogger(__name__)
router = Router()


def _lang_select_kb(current_lang: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора языка."""
    ru_mark = " ✅" if current_lang == "ru" else ""
    en_mark = " ✅" if current_lang == "en" else ""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🇷🇺 Русский{ru_mark}", callback_data="lang:ru")],
        [InlineKeyboardButton(text=f"🇬🇧 English{en_mark}", callback_data="lang:en")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
    ])


@router.callback_query(F.data == "menu:settings")
async def cb_settings(callback: CallbackQuery, **kwargs):
    """Показать настройки языка."""
    uid = callback.from_user.id
    lang = get_user_lang(uid)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        t("lang_select", lang),
        parse_mode="Markdown",
        reply_markup=_lang_select_kb(lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def cb_set_lang(callback: CallbackQuery, **kwargs):
    """Установить язык."""
    lang = callback.data.split(":")[1]
    uid = callback.from_user.id

    set_user_lang(uid, lang)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        t("lang_set", lang) + "\n\n" + t("main_menu", lang),
        parse_mode="Markdown",
        reply_markup=get_menu_kb(uid),
    )
    await callback.answer()
