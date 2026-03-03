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
from handlers.favorites import router as favorites_router
from handlers.templates import router as templates_router
from handlers.export import router as export_router
from handlers.settings import router as settings_router
from handlers.voice import router as voice_router
from handlers.file_upload import router as file_upload_router
from handlers.admin_panel import router as admin_panel_router
from handlers.admin_whitelist import router as admin_wl_router
from handlers.admin_agents import router as admin_ag_router
from handlers.admin_stats import router as admin_stats_router
# ── Новые хендлеры ───────────────────────────────────────
from handlers.web_search import router as web_search_router
from handlers.multi_agent import router as multi_agent_router
from handlers.scheduled import router as scheduled_router
from handlers.memory import router as memory_router
from handlers.charts import router as charts_router
from handlers.knowledge import router as knowledge_router
from handlers.market import router as market_router
# ── Catch-all — ПОСЛЕДНИЙ ────────────────────────────────
from handlers.chat_router import router as chat_router

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

    # Инициализация новых таблиц
    from db.memory import init_memory_table
    from db.scheduled import init_scheduled_table
    from db.knowledge import init_knowledge_table
    init_memory_table()
    init_scheduled_table()
    init_knowledge_table()
    logger.info("New tables initialized (memory, scheduled, knowledge)")

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

    # Регистрация роутеров (порядок важен!)
    # 1. Команды и навигация
    dp.include_router(start_router)
    dp.include_router(menu_nav_router)
    # 2. Агенты и их фичи
    dp.include_router(agents_router)
    dp.include_router(favorites_router)
    dp.include_router(templates_router)
    dp.include_router(export_router)

    # 3. Новые фичи (FSM-роутеры — перед свободным чатом!)
    dp.include_router(web_search_router)
    dp.include_router(multi_agent_router)
    dp.include_router(scheduled_router)
    dp.include_router(memory_router)
    dp.include_router(charts_router)
    dp.include_router(knowledge_router)
    dp.include_router(market_router)

    # 4. Свободный чат
    dp.include_router(free_chat_router)
    # 5. Настройки
    dp.include_router(settings_router)
    # 6. Голосовые и файлы
    dp.include_router(voice_router)
    dp.include_router(file_upload_router)
    # 7. Админка
    dp.include_router(admin_panel_router)
    dp.include_router(admin_wl_router)
    dp.include_router(admin_ag_router)
    dp.include_router(admin_stats_router)
    # 8. Catch-all текстовый роутер — ПОСЛЕДНИЙ
    dp.include_router(chat_router)

    # Инициализация планировщика
    from services.scheduler import init_scheduler
    await init_scheduler(bot)
    logger.info("Scheduler initialized")

    # Запуск
    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        from services.scheduler import stop_scheduler
        stop_scheduler()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
