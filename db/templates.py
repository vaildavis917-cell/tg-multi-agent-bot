"""
Шаблоны быстрых запросов для агентов.
"""

import time
from typing import Optional
from db.connection import get_connection


def add_template(agent_id: int, title: str, text: str) -> int:
    """Добавить шаблон. Возвращает ID."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO templates (agent_id, title, text, created_at) VALUES (?,?,?,?)",
            (agent_id, title, text, time.time()),
        )
        return cur.lastrowid


def get_templates(agent_id: int) -> list[dict]:
    """Получить все шаблоны агента."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM templates WHERE agent_id=? ORDER BY id",
            (agent_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_template(template_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM templates WHERE id=?", (template_id,)
        ).fetchone()
        return dict(row) if row else None


def delete_template(template_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM templates WHERE id=?", (template_id,))
        return cur.rowcount > 0
