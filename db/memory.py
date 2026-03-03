"""
БД-слой для долгосрочной памяти агентов.
Хранит ключевые факты о пользователе между сессиями.
"""

import logging
from datetime import datetime
from db.connection import get_connection

logger = logging.getLogger(__name__)


def init_memory_table():
    """Создаёт таблицу памяти агентов."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                fact TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_user_agent
            ON agent_memory(user_id, agent_id)
        """)


def save_memory(user_id: int, agent_id: int, fact: str, category: str = "general"):
    """Сохраняет факт в память агента."""
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO agent_memory (user_id, agent_id, fact, category, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, agent_id, fact, category, now, now),
        )


def get_memories(user_id: int, agent_id: int, limit: int = 20) -> list[dict]:
    """Возвращает факты из памяти агента для пользователя."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_memory WHERE user_id = ? AND agent_id = ? "
            "ORDER BY updated_at DESC LIMIT ?",
            (user_id, agent_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_user_memories(user_id: int, limit: int = 50) -> list[dict]:
    """Возвращает все факты пользователя от всех агентов."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_memory WHERE user_id = ? "
            "ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_memory(memory_id: int):
    """Удаляет конкретный факт."""
    with get_connection() as conn:
        conn.execute("DELETE FROM agent_memory WHERE id = ?", (memory_id,))


def clear_agent_memory(user_id: int, agent_id: int):
    """Очищает всю память агента для пользователя."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM agent_memory WHERE user_id = ? AND agent_id = ?",
            (user_id, agent_id),
        )


def clear_all_memory(user_id: int):
    """Очищает всю память пользователя."""
    with get_connection() as conn:
        conn.execute("DELETE FROM agent_memory WHERE user_id = ?", (user_id,))


def format_memories_for_context(memories: list[dict]) -> str:
    """Форматирует память для добавления в системный промпт."""
    if not memories:
        return ""

    parts = ["\n[ДОЛГОСРОЧНАЯ ПАМЯТЬ — факты о пользователе из предыдущих сессий:]"]
    for m in memories:
        parts.append(f"• [{m['category']}] {m['fact']}")
    parts.append("[КОНЕЦ ПАМЯТИ]\n")

    return "\n".join(parts)
