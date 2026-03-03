"""
Избранные агенты пользователя.
"""

import time
from db.connection import get_connection


def add_favorite(user_id: int, agent_id: int) -> bool:
    """Добавить агента в избранное. Возвращает True если добавлен."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id=? AND agent_id=?",
            (user_id, agent_id),
        ).fetchone()
        if existing:
            return False
        conn.execute(
            "INSERT INTO favorites (user_id, agent_id, added_at) VALUES (?,?,?)",
            (user_id, agent_id, time.time()),
        )
        return True


def remove_favorite(user_id: int, agent_id: int) -> bool:
    """Убрать агента из избранного."""
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM favorites WHERE user_id=? AND agent_id=?",
            (user_id, agent_id),
        )
        return cur.rowcount > 0


def get_favorites(user_id: int) -> list[int]:
    """Возвращает список agent_id в избранном."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT agent_id FROM favorites WHERE user_id=? ORDER BY added_at",
            (user_id,),
        ).fetchall()
        return [r["agent_id"] for r in rows]


def is_favorite(user_id: int, agent_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id=? AND agent_id=?",
            (user_id, agent_id),
        ).fetchone()
        return row is not None
