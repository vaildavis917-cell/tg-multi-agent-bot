"""
CRUD-операции для whitelist пользователей.
Поддержка тегов (имён/заметок) рядом с user_id.
"""

import time
import sqlite3
from db.connection import get_connection


def add_to_whitelist(user_id: int, tag: str = "", username: str = "", full_name: str = "", added_by: int = 0) -> bool:
    with get_connection() as conn:
        try:
            conn.execute(
                "INSERT INTO whitelist (user_id, tag, username, full_name, added_by, added_at, is_active) "
                "VALUES (?, ?, ?, ?, ?, ?, 1)",
                (user_id, tag, username, full_name, added_by, time.time()),
            )
            return True
        except sqlite3.IntegrityError:
            conn.execute(
                "UPDATE whitelist SET is_active=1, tag=?, username=?, full_name=?, added_by=?, added_at=? WHERE user_id=?",
                (tag, username, full_name, added_by, time.time(), user_id),
            )
            return True


def update_tag(user_id: int, tag: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("UPDATE whitelist SET tag=? WHERE user_id=? AND is_active=1", (tag, user_id))
        return cur.rowcount > 0


def remove_from_whitelist(user_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("UPDATE whitelist SET is_active=0 WHERE user_id=? AND is_active=1", (user_id,))
        return cur.rowcount > 0


def is_whitelisted(user_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM whitelist WHERE user_id=? AND is_active=1", (user_id,)).fetchone()
        return row is not None


def get_whitelist() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT user_id, tag, username, full_name, added_by, added_at "
            "FROM whitelist WHERE is_active=1 ORDER BY added_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_whitelist_user(user_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT user_id, tag, username, full_name, added_by, added_at "
            "FROM whitelist WHERE user_id=? AND is_active=1", (user_id,)
        ).fetchone()
        return dict(row) if row else None
