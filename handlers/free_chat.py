"""
Хендлеры режима свободного чата с LLM.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from db.state import set_user_state
from db.history import clear_history
from keyboards import free_chat_kb

router = Router()


@router.message(Command("free"))
async def cmd_free(message: Message, **kwargs):
    set_user_state(message.from_user.id, "free_chat")
    await message.answer(
        "💬 **Свободный чат с Claude Opus 4.6**\n\n"
        "Пишите сообщения — бот ответит без системного промпта агента.",
        parse_mode="Markdown",
        reply_markup=free_chat_kb(),
    )


@router.callback_query(F.data == "menu:free_chat")
async def cb_free(callback: CallbackQuery, **kwargs):
    set_user_state(callback.from_user.id, "free_chat")
    await callback.message.edit_text(
        "💬 **Свободный чат с Claude Opus 4.6**\n\n"
        "Пишите сообщения — бот ответит без системного промпта агента.",
        parse_mode="Markdown",
        reply_markup=free_chat_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "free:clear")
async def cb_free_clear(callback: CallbackQuery, **kwargs):
    clear_history(callback.from_user.id, agent_id=None)
    await callback.message.edit_text(
        "🔄 Диалог сброшен.\n\n"
        "💬 **Свободный чат с Claude Opus 4.6**\n\nМожете начать заново.",
        parse_mode="Markdown",
        reply_markup=free_chat_kb(),
    )
    await callback.answer()
