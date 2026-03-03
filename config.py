"""
Конфигурация бота. Все секреты загружаются из .env.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ─────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

# ── OpenRouter ───────────────────────────────────────────
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY")
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-opus-4.6")

# ── Админы ───────────────────────────────────────────────
ADMIN_IDS: list[int] = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))

# ── SQLite ───────────────────────────────────────────────
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bot_data.db")

# ── Лимиты ───────────────────────────────────────────────
MAX_HISTORY_LENGTH: int = int(os.getenv("MAX_HISTORY_LENGTH", "20"))
MAX_MESSAGE_LENGTH: int = 4096

# ── Alpha Vantage ────────────────────────────────────────
ALPHA_VANTAGE_KEY: str = os.getenv("ALPHA_VANTAGE_KEY", "")
