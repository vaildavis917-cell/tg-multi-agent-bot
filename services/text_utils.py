"""
Утилиты для работы с текстом (разбивка длинных сообщений и т.д.).
"""

from config import MAX_MESSAGE_LENGTH


def split_text(text: str, max_len: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Разбивает текст на части, не превышающие max_len символов."""
    parts: list[str] = []
    while len(text) > max_len:
        pos = text.rfind("\n", 0, max_len)
        if pos == -1:
            pos = text.rfind(" ", 0, max_len)
        if pos == -1:
            pos = max_len
        parts.append(text[:pos])
        text = text[pos:].lstrip()
    if text:
        parts.append(text)
    return parts
