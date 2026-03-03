"""
RAG (Retrieval-Augmented Generation) — семантический поиск по базе знаний.
Использует простые TF-IDF эмбеддинги для поиска релевантных чанков.
Для продакшена можно заменить на OpenAI embeddings.
"""

import logging
import math
import re
from collections import Counter
from typing import Optional

from db.knowledge import add_document, add_chunk, get_all_chunks, get_user_documents

logger = logging.getLogger(__name__)

# Размер чанка в символах
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 5


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Разбивает текст на чанки с перекрытием."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Ищем конец предложения для красивого разрыва
        if end < len(text):
            # Ищем точку, перенос строки или конец абзаца
            for sep in ["\n\n", "\n", ". ", "! ", "? "]:
                pos = text.rfind(sep, start + chunk_size // 2, end + 100)
                if pos > start:
                    end = pos + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def _tokenize(text: str) -> list[str]:
    """Простая токенизация для TF-IDF."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    # Убираем стоп-слова (минимальный набор)
    stop_words = {
        'и', 'в', 'на', 'с', 'по', 'для', 'от', 'к', 'из', 'о', 'об',
        'что', 'как', 'это', 'не', 'но', 'а', 'или', 'то', 'же', 'бы',
        'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and',
        'is', 'it', 'that', 'this', 'with', 'by', 'from', 'are', 'was',
    }
    return [t for t in tokens if t not in stop_words and len(t) > 1]


def _compute_tfidf(text: str, corpus_tokens: list[list[str]]) -> dict[str, float]:
    """Вычисляет TF-IDF вектор для текста."""
    tokens = _tokenize(text)
    tf = Counter(tokens)
    total = len(tokens) if tokens else 1

    tfidf = {}
    n_docs = len(corpus_tokens) + 1  # +1 для сглаживания

    for token, count in tf.items():
        # TF
        term_freq = count / total
        # IDF
        doc_freq = sum(1 for doc in corpus_tokens if token in doc) + 1
        idf = math.log(n_docs / doc_freq)
        tfidf[token] = term_freq * idf

    return tfidf


def _cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
    """Косинусное сходство между двумя TF-IDF векторами."""
    common_keys = set(vec1.keys()) & set(vec2.keys())
    if not common_keys:
        return 0.0

    dot_product = sum(vec1[k] * vec2[k] for k in common_keys)
    norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


async def index_document(user_id: int, filename: str, content: str, file_type: str = "text") -> int:
    """
    Индексирует документ: разбивает на чанки и сохраняет.
    Возвращает количество чанков.
    """
    # Сохраняем документ
    doc_id = add_document(user_id, filename, content, file_type)

    # Разбиваем на чанки
    chunks = chunk_text(content)

    # Сохраняем чанки (без эмбеддингов — используем TF-IDF на лету)
    for i, chunk in enumerate(chunks):
        add_chunk(doc_id, user_id, chunk, embedding=[], chunk_index=i)

    logger.info("Indexed document '%s': %d chunks", filename, len(chunks))
    return len(chunks)


def search_knowledge_base(user_id: int, query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Семантический поиск по базе знаний пользователя.
    Возвращает top_k наиболее релевантных чанков.
    """
    chunks = get_all_chunks(user_id)
    if not chunks:
        return []

    # Токенизируем все чанки для IDF
    corpus_tokens = [_tokenize(c["chunk_text"]) for c in chunks]

    # TF-IDF для запроса
    query_vec = _compute_tfidf(query, corpus_tokens)

    # Считаем сходство с каждым чанком
    scored = []
    for i, chunk in enumerate(chunks):
        chunk_vec = _compute_tfidf(chunk["chunk_text"], corpus_tokens)
        score = _cosine_similarity(query_vec, chunk_vec)
        scored.append({
            "chunk_text": chunk["chunk_text"],
            "doc_id": chunk["doc_id"],
            "score": score,
        })

    # Сортируем по релевантности
    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[:top_k]


def format_rag_context(results: list[dict]) -> str:
    """Форматирует результаты RAG для добавления в контекст LLM."""
    if not results:
        return ""

    parts = ["\n[КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ ПОЛЬЗОВАТЕЛЯ:]"]
    for i, r in enumerate(results, 1):
        if r["score"] > 0.01:  # Фильтруем нерелевантные
            parts.append(f"\n--- Фрагмент {i} (релевантность: {r['score']:.2f}) ---")
            parts.append(r["chunk_text"][:800])

    if len(parts) == 1:
        return ""

    parts.append("\n[КОНЕЦ КОНТЕКСТА ИЗ БАЗЫ ЗНАНИЙ]\n")
    return "\n".join(parts)
