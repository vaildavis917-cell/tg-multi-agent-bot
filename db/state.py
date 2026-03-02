"""
Хранение текущего состояния пользователя (выбранный режим / агент).
"""

import time
from typing import Optional
from db.connection import get_connection


def get_user_state(user_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM user_state WHERE user_id=?", (user_id,)).fetchone()
        if row:
            return dict(row)
        conn.execute(
            "INSERT INTO user_state (user_id, current_mode, current_agent_id, updated_at) VALUES (?,'menu',NULL,?)",
            (user_id, time.time()),
        )
        return {"user_id": user_id, "current_mode": "menu", "current_agent_id": None}


def set_user_state(user_id: int, mode: str, agent_id: Optional[int] = None) -> None:
    now = time.time()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO user_state (user_id, current_mode, current_agent_id, updated_at) "
            "VALUES (?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET current_mode=?, current_agent_id=?, updated_at=?",
            (user_id, mode, agent_id, now, mode, agent_id, now),
        )
