"""
Подключение к SQLite и инициализация схемы.
"""

import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH


@contextmanager
def get_connection():
    """Context manager для соединения с БД."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Создание всех таблиц при первом запуске."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS whitelist (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT DEFAULT '',
                full_name   TEXT DEFAULT '',
                tag         TEXT DEFAULT '',
                added_by    INTEGER DEFAULT 0,
                added_at    REAL DEFAULT 0,
                is_active   INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS agents (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL UNIQUE,
                emoji           TEXT DEFAULT '🤖',
                description     TEXT DEFAULT '',
                system_prompt   TEXT DEFAULT '',
                is_active       INTEGER DEFAULT 1,
                created_at      REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                agent_id    INTEGER DEFAULT NULL,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                created_at  REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS usage_stats (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                agent_id    INTEGER DEFAULT NULL,
                tokens_in   INTEGER DEFAULT 0,
                tokens_out  INTEGER DEFAULT 0,
                created_at  REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_state (
                user_id             INTEGER PRIMARY KEY,
                current_mode        TEXT DEFAULT 'menu',
                current_agent_id    INTEGER DEFAULT NULL,
                updated_at          REAL DEFAULT 0
            );
        """)

        # Миграция: добавляем колонку tag если её нет
        try:
            conn.execute("ALTER TABLE whitelist ADD COLUMN tag TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # колонка уже существует
