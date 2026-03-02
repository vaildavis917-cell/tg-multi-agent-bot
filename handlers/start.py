"""
Хендлеры: /start, /menu, /help.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from db.state import set_user_state
from keyboards import get_menu_kb

router = Router()

WELCOME = (
    "🤖 **Мульти-агентный AI бот**\n\n"
    "Добро пожаловать! Этот бот предоставляет доступ к AI-агентам "
    "на базе Claude Opus 4.6.\n\n"
    "Выберите действие:"
)

HELP = (
    "ℹ️ **Помощь**\n\n"
    "**Команды:**\n"
    "/start — Главное меню\n"
    "/menu — Открыть меню\n"
    "/help — Эта справка\n"
    "/agents — Список агентов\n"
    "/free — Свободный чат с LLM\n"
    "/clear — Сбросить историю\n\n"
    "**Как пользоваться:**\n"
    "1. Выберите агента или свободный чат\n"
    "2. Пишите сообщения — бот ответит через AI\n"
    "3. /clear — сброс контекста\n"
    "4. /menu — возврат в меню"
)


@router.message(Command("start"))
async def cmd_start(message: Message, **kwargs):
    set_user_state(message.from_user.id, "menu")
    await message.answer(WELCOME, parse_mode="Markdown", reply_markup=get_menu_kb(message.from_user.id))


@router.message(Command("menu"))
async def cmd_menu(message: Message, **kwargs):
    set_user_state(message.from_user.id, "menu")
    await message.answer("📋 **Главное меню:**", parse_mode="Markdown", reply_markup=get_menu_kb(message.from_user.id))


@router.message(Command("help"))
async def cmd_help(message: Message, **kwargs):
    await message.answer(HELP, parse_mode="Markdown")
