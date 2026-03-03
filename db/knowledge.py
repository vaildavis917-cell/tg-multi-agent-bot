"""
БД-слой для RAG — база знаний с эмбеддингами.
Хранит документы, чанки и их эмбеддинги для семантического поиска.
"""

import json
import logging
from datetime import datetime
from db.connection import get_connection

logger = logging.getLogger(__name__)


def init_knowledge_table():
    """Создаёт таблицы для базы знаний."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kb_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT DEFAULT 'text',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kb_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding TEXT,
                chunk_index INTEGER DEFAULT 0,
                FOREIGN KEY (doc_id) REFERENCES kb_documents(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_user
            ON kb_chunks(user_id)
        """)


def add_document(user_id: int, filename: str, content: str, file_type: str = "text") -> int:
    """Добавляет документ. Возвращает ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO kb_documents (user_id, filename, file_type, content, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, filename, file_type, content, datetime.now().isoformat()),
        )
        return cursor.lastrowid


def add_chunk(doc_id: int, user_id: int, chunk_text: str, embedding: list[float], chunk_index: int = 0):
    """Добавляет чанк с эмбеддингом."""
    embedding_json = json.dumps(embedding) if embedding else None
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO kb_chunks (doc_id, user_id, chunk_text, embedding, chunk_index) "
            "VALUES (?, ?, ?, ?, ?)",
            (doc_id, user_id, chunk_text, embedding_json, chunk_index),
        )


def get_user_documents(user_id: int) -> list[dict]:
    """Возвращает документы пользователя."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, filename, file_type, created_at, LENGTH(content) as size "
            "FROM kb_documents WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_chunks(user_id: int) -> list[dict]:
    """Возвращает все чанки пользователя с эмбеддингами."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, doc_id, chunk_text, embedding FROM kb_chunks WHERE user_id = ?",
            (user_id,),
        ).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        if d["embedding"]:
            d["embedding"] = json.loads(d["embedding"])
        result.append(d)
    return result


def delete_document(doc_id: int):
    """Удаляет документ и его чанки."""
    with get_connection() as conn:
        conn.execute("DELETE FROM kb_chunks WHERE doc_id = ?", (doc_id,))
        conn.execute("DELETE FROM kb_documents WHERE id = ?", (doc_id,))


def clear_knowledge_base(user_id: int):
    """Очищает всю базу знаний пользователя."""
    with get_connection() as conn:
        conn.execute("DELETE FROM kb_chunks WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM kb_documents WHERE user_id = ?", (user_id,))
