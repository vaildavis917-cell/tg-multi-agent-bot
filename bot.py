"""
Точка входа — сборка и запуск бота.
"""

import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import TELEGRAM_BOT_TOKEN
from db.connection import init_db

# ── Хендлеры (каждый в своём файле) ──────────────────────
from handlers.start import router as start_router
from handlers.menu_nav import router as menu_nav_router
from handlers.agents import router as agents_router
from handlers.free_chat import router as free_chat_router
from handlers.admin_panel import router as admin_panel_router
from handlers.admin_whitelist import router as admin_wl_router
from handlers.admin_agents import router as admin_ag_router
from handlers.admin_stats import router as admin_stats_router
from handlers.chat_router import router as chat_router  # ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ

# ── Middleware ───────────────────────────────────────────
from middlewares import AccessMiddleware, LoggingMiddleware


def setup_logging():
    """Настройка логирования в файл + stdout."""
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/bot.log", encoding="utf-8"),
        ],
    )


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    # Инициализация БД
    init_db()
    logger.info("Database initialized")

    # Бот и диспетчер
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=None),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware (порядок важен)
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(AccessMiddleware())
    dp.callback_query.middleware(AccessMiddleware())

    # Регистрация роутеров (порядок важен — chat_router последний!)
    dp.include_router(start_router)
    dp.include_router(menu_nav_router)
    dp.include_router(agents_router)
    dp.include_router(free_chat_router)
    dp.include_router(admin_panel_router)
    dp.include_router(admin_wl_router)
    dp.include_router(admin_ag_router)
    dp.include_router(admin_stats_router)
    dp.include_router(chat_router)  # catch-all — последний

    # Запуск
    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
