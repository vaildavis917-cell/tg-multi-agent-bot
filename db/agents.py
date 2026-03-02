"""
CRUD-операции для AI-агентов.
"""

import time
from typing import Optional
from db.connection import get_connection


def add_agent(name: str, emoji: str, description: str, system_prompt: str) -> int:
    """Добавить агента. Возвращает ID."""
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO agents (name, emoji, description, system_prompt, is_active, created_at) "
            "VALUES (?, ?, ?, ?, 1, ?)",
            (name, emoji, description, system_prompt, time.time()),
        )
        return cur.lastrowid


def update_agent(agent_id: int, **kwargs) -> bool:
    """Обновить поля агента (name, emoji, description, system_prompt, is_active)."""
    allowed = {"name", "emoji", "description", "system_prompt", "is_active"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return False
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [agent_id]
    with get_connection() as conn:
        cur = conn.execute(f"UPDATE agents SET {set_clause} WHERE id=?", values)
        return cur.rowcount > 0


def delete_agent(agent_id: int) -> bool:
    """Soft-delete агента."""
    with get_connection() as conn:
        cur = conn.execute("UPDATE agents SET is_active=0 WHERE id=?", (agent_id,))
        return cur.rowcount > 0


def get_agents(active_only: bool = True) -> list[dict]:
    with get_connection() as conn:
        q = "SELECT * FROM agents"
        if active_only:
            q += " WHERE is_active=1"
        q += " ORDER BY id"
        return [dict(r) for r in conn.execute(q).fetchall()]


def get_agent(agent_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
        return dict(row) if row else None
