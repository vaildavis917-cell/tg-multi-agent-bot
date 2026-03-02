"""
Админ-панель: просмотр статистики.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import ADMIN_IDS
from db.stats import get_stats_summary
from keyboards import admin_panel_kb

router = Router()


@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery, **kwargs):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("🚫 Нет доступа", show_alert=True)
        return

    s = get_stats_summary()
    await callback.message.edit_text(
        "📊 **Статистика бота**\n\n"
        f"👥 Пользователей в whitelist: **{s['whitelist_count']}**\n"
        f"🤖 Активных агентов: **{s['agents_count']}**\n"
        f"💬 Всего сообщений: **{s['total_messages']}**\n"
        f"👤 Уникальных пользователей: **{s['total_users']}**\n"
        f"📥 Токенов (вход): **{s['total_tokens_in']:,}**\n"
        f"📤 Токенов (выход): **{s['total_tokens_out']:,}**",
        parse_mode="Markdown",
        reply_markup=admin_panel_kb(),
    )
    await callback.answer()
