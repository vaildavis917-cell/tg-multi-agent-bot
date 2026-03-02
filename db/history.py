"""
Работа с историей диалогов.
"""

import time
from typing import Optional
from db.connection import get_connection


def save_message(user_id: int, role: str, content: str, agent_id: Optional[int] = None) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_history (user_id, agent_id, role, content, created_at) VALUES (?,?,?,?,?)",
            (user_id, agent_id, role, content, time.time()),
        )


def get_history(user_id: int, agent_id: Optional[int] = None, limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        if agent_id is not None:
            rows = conn.execute(
                "SELECT role, content FROM chat_history "
                "WHERE user_id=? AND agent_id=? ORDER BY id DESC LIMIT ?",
                (user_id, agent_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT role, content FROM chat_history "
                "WHERE user_id=? AND agent_id IS NULL ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]


def clear_history(user_id: int, agent_id: Optional[int] = None) -> int:
    """Возвращает количество удалённых записей."""
    with get_connection() as conn:
        if agent_id is not None:
            cur = conn.execute(
                "DELETE FROM chat_history WHERE user_id=? AND agent_id=?", (user_id, agent_id)
            )
        else:
            cur = conn.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))
        return cur.rowcount
