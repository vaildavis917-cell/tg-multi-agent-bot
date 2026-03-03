"""
Настройки пользователя (язык и т.д.).
"""

import time
from typing import Optional
from db.connection import get_connection


def get_user_lang(user_id: int) -> str:
    """Получить язык пользователя. По умолчанию 'ru'."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT lang FROM user_settings WHERE user_id=?", (user_id,)
        ).fetchone()
        return row["lang"] if row else "ru"


def set_user_lang(user_id: int, lang: str) -> None:
    """Установить язык пользователя."""
    now = time.time()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO user_settings (user_id, lang, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET lang=?, updated_at=?",
            (user_id, lang, now, lang, now),
        )


def get_user_settings(user_id: int) -> dict:
    """Получить все настройки пользователя."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM user_settings WHERE user_id=?", (user_id,)
        ).fetchone()
        if row:
            return dict(row)
        return {"user_id": user_id, "lang": "ru"}
