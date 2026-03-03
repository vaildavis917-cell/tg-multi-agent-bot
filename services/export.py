"""
Экспорт диалогов в текстовый файл.
"""

import os
import tempfile
import time
from typing import Optional

from db.history import get_history
from db.agents import get_agent


def export_dialog_to_file(
    user_id: int,
    agent_id: Optional[int] = None,
    limit: int = 500,
) -> Optional[str]:
    """
    Экспортирует диалог в .txt файл.
    Возвращает путь к файлу или None если история пуста.
    """
    history = get_history(user_id, agent_id, limit)
    if not history:
        return None

    # Заголовок
    if agent_id:
        agent = get_agent(agent_id)
        title = f"Диалог с агентом: {agent['emoji']} {agent['name']}" if agent else "Диалог с агентом"
    else:
        title = "Свободный чат с Claude"

    lines = [
        f"{'=' * 50}",
        f"  {title}",
        f"  Экспорт: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Сообщений: {len(history)}",
        f"{'=' * 50}",
        "",
    ]

    for msg in history:
        role_label = "👤 Вы" if msg["role"] == "user" else "🤖 AI"
        lines.append(f"── {role_label} ──")
        lines.append(msg["content"])
        lines.append("")

    lines.append(f"{'=' * 50}")
    lines.append("Конец диалога")

    content = "\n".join(lines)

    # Сохраняем во временный файл
    tmp_dir = tempfile.mkdtemp(prefix="tgbot_export_")
    safe_title = "dialog"
    if agent_id:
        safe_title = f"agent_{agent_id}"
    filename = f"export_{safe_title}_{int(time.time())}.txt"
    filepath = os.path.join(tmp_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath
