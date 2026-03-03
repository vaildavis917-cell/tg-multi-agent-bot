"""
Хендлер загрузки файлов (PDF, Excel, CSV, TXT).
Парсит файл и добавляет содержимое в контекст текущего агента/чата.
"""

import os
import logging
import tempfile

from aiogram import Router, Bot
from aiogram.types import Message

from config import MAX_HISTORY_LENGTH
from db.state import get_user_state, set_user_state
from db.agents import get_agent
from db.history import save_message, get_history
from db.stats import log_usage
from services.file_parser import parse_file
from services.llm_stream import chat_completion_stream
from services.text_utils import split_text
from keyboards import get_menu_kb, agent_selected_kb, free_chat_kb

logger = logging.getLogger(__name__)
router = Router()

SUPPORTED_EXTENSIONS = {".txt", ".csv", ".xlsx", ".xls", ".pdf"}

FREE_CHAT_PROMPT = (
    "Ты — универсальный AI-ассистент Claude. "
    "Отвечай подробно, точно и полезно. "
    "Используй русский язык, если пользователь пишет на русском."
)


@router.message(lambda msg: msg.document is not None)
async def on_document(message: Message, bot: Bot, **kwargs):
    """Обрабатывает загруженные документы."""
    uid = message.from_user.id
    doc = message.document

    # Проверяем расширение
    filename = doc.file_name or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        await message.answer(
            f"❌ Формат `{ext}` не поддерживается.\n\n"
            f"Поддерживаемые: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            parse_mode="Markdown",
        )
        return

    # Проверяем размер (макс 20 MB)
    if doc.file_size and doc.file_size > 20 * 1024 * 1024:
        await message.answer("❌ Файл слишком большой (макс 20 MB).")
        return

    # Скачиваем
    status_msg = await message.answer(f"📎 Обрабатываю файл `{filename}`...", parse_mode="Markdown")

    file = await bot.get_file(doc.file_id)
    tmp_dir = tempfile.mkdtemp(prefix="tgbot_file_")
    local_path = os.path.join(tmp_dir, filename)
    await bot.download_file(file.file_path, local_path)

    # Парсим
    text = parse_file(local_path)

    # Чистим
    try:
        os.remove(local_path)
        os.rmdir(tmp_dir)
    except Exception:
        pass

    if not text:
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer("❌ Не удалось извлечь текст из файла.")
        return

    # Определяем режим
    state = get_user_state(uid)
    mode = state["current_mode"]

    if mode == "agent":
        agent_id = state.get("current_agent_id")
        agent = get_agent(agent_id) if agent_id else None
        if not agent:
            set_user_state(uid, "menu")
            try:
                await status_msg.delete()
            except Exception:
                pass
            await message.answer("❌ Агент не найден. Возвращаю в меню.", reply_markup=get_menu_kb(uid))
            return
        system_prompt = agent["system_prompt"]
        reply_kb = agent_selected_kb(agent_id)
    elif mode == "free_chat":
        agent_id = None
        system_prompt = FREE_CHAT_PROMPT
        reply_kb = free_chat_kb()
    else:
        try:
            await status_msg.delete()
        except Exception:
            pass
        await message.answer(
            "Сначала выберите режим через меню 👇",
            reply_markup=get_menu_kb(uid),
        )
        return

    # Формируем сообщение с контекстом файла
    user_text = message.caption or ""
    file_context = (
        f"📎 Пользователь загрузил файл: {filename}\n\n"
        f"--- СОДЕРЖИМОЕ ФАЙЛА ---\n{text}\n--- КОНЕЦ ФАЙЛА ---"
    )
    if user_text:
        file_context = f"{user_text}\n\n{file_context}"

    save_message(uid, "user", file_context, agent_id)

    history = get_history(uid, agent_id, MAX_HISTORY_LENGTH)
    messages = [{"role": m["role"], "content": m["content"]} for m in history]

    try:
        await status_msg.edit_text(f"📎 Файл `{filename}` загружен ({len(text)} символов).\n\n⏳ Анализирую...", parse_mode="Markdown")
    except Exception:
        pass

    final_content = ""
    got_error = False

    async for event in chat_completion_stream(messages=messages, system_prompt=system_prompt):
        etype = event["type"]
        if etype == "error":
            final_content = event["content"]
            got_error = True
            break
        if etype == "done":
            final_content = event["content"]
            tokens_in = event.get("tokens_in", 0)
            tokens_out = event.get("tokens_out", 0)
            save_message(uid, "assistant", final_content, agent_id)
            log_usage(uid, agent_id, tokens_in, tokens_out)
            break

    try:
        await status_msg.delete()
    except Exception:
        pass

    if got_error:
        await message.answer(final_content, reply_markup=reply_kb)
        return

    parts = split_text(final_content)
    for i, part in enumerate(parts):
        kb = reply_kb if i == len(parts) - 1 else None
        try:
            await message.answer(part, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await message.answer(part, reply_markup=kb)
