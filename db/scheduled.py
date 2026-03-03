"""
БД-слой для запланированных отчётов.
"""

import logging
from datetime import datetime
from db.connection import get_connection

logger = logging.getLogger(__name__)


def init_scheduled_table():
    """Создаёт таблицу запланированных отчётов."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                cron_expr TEXT NOT NULL DEFAULT '0 9 * * *',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_run TEXT
            )
        """)


def add_schedule(user_id: int, agent_id: int, prompt: str, cron_expr: str = "0 9 * * *") -> int:
    """Добавляет новый запланированный отчёт. Возвращает ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO scheduled_reports (user_id, agent_id, prompt, cron_expr, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, agent_id, prompt, cron_expr, datetime.now().isoformat()),
        )
        return cursor.lastrowid


def get_user_schedules(user_id: int) -> list[dict]:
    """Возвращает все расписания пользователя."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_reports WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_schedules() -> list[dict]:
    """Возвращает все активные расписания."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM scheduled_reports WHERE active = 1"
        ).fetchall()
        return [dict(r) for r in rows]


def get_schedule(schedule_id: int) -> dict | None:
    """Возвращает расписание по ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM scheduled_reports WHERE id = ?",
            (schedule_id,),
        ).fetchone()
        return dict(row) if row else None


def toggle_schedule(schedule_id: int) -> bool:
    """Переключает активность расписания. Возвращает новое состояние."""
    with get_connection() as conn:
        row = conn.execute("SELECT active FROM scheduled_reports WHERE id = ?", (schedule_id,)).fetchone()
        if not row:
            return False
        new_active = 0 if row["active"] else 1
        conn.execute("UPDATE scheduled_reports SET active = ? WHERE id = ?", (new_active, schedule_id))
        return bool(new_active)


def delete_schedule(schedule_id: int):
    """Удаляет расписание."""
    with get_connection() as conn:
        conn.execute("DELETE FROM scheduled_reports WHERE id = ?", (schedule_id,))


def update_last_run(schedule_id: int):
    """Обновляет время последнего запуска."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE scheduled_reports SET last_run = ? WHERE id = ?",
            (datetime.now().isoformat(), schedule_id),
        )
