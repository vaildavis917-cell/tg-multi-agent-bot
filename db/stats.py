"""
Логирование и получение статистики использования.
"""

import time
from typing import Optional
from db.connection import get_connection


def log_usage(user_id: int, agent_id: Optional[int], tokens_in: int, tokens_out: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO usage_stats (user_id, agent_id, tokens_in, tokens_out, created_at) VALUES (?,?,?,?,?)",
            (user_id, agent_id, tokens_in, tokens_out, time.time()),
        )


def get_stats_summary() -> dict:
    with get_connection() as conn:
        total_messages = conn.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0]
        total_users = conn.execute("SELECT COUNT(DISTINCT user_id) FROM chat_history").fetchone()[0]
        tokens_in = conn.execute("SELECT COALESCE(SUM(tokens_in),0) FROM usage_stats").fetchone()[0]
        tokens_out = conn.execute("SELECT COALESCE(SUM(tokens_out),0) FROM usage_stats").fetchone()[0]
        wl_count = conn.execute("SELECT COUNT(*) FROM whitelist WHERE is_active=1").fetchone()[0]
        agents_count = conn.execute("SELECT COUNT(*) FROM agents WHERE is_active=1").fetchone()[0]
        return {
            "total_messages": total_messages,
            "total_users": total_users,
            "total_tokens_in": tokens_in,
            "total_tokens_out": tokens_out,
            "whitelist_count": wl_count,
            "agents_count": agents_count,
        }
