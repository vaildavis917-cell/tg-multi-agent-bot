"""
Хендлер голосовых сообщений.
Транскрибирует голос → отправляет текст в LLM → возвращает ответ.
"""

import os
import logging
import tempfile

from aiogram import Router, Bot
from aiogram.types import Message

from config import MAX_HISTORY_LENGTH, MAX_MESSAGE_LENGTH
from db.state import get_user_state, set_user_state
from db.agents import get_agent
from db.history import get_history, save_message
from db.stats import log_usage
from services.stt import transcribe_voice
from services.llm_stream import chat_completion_stream
from services.text_utils import split_text
from keyboards import get_menu_kb, agent_selected_kb, free_chat_kb

logger = logging.getLogger(__name__)
router = Router()

FREE_CHAT_PROMPT = (
    "Ты — универсальный AI-ассистент Claude. "
    "Отвечай подробно, точно и полезно. "
    "Используй русский язык, если пользователь пишет на русском."
)


@router.message(lambda msg: msg.voice is not None or msg.audio is not None)
async def on_voice_message(message: Message, bot: Bot, **kwargs):
    """Обрабатывает голосовые и аудио сообщения."""
    uid = message.from_user.id

    # Скачиваем файл
    if message.voice:
        file = await bot.get_file(message.voice.file_id)
    else:
        file = await bot.get_file(message.audio.file_id)

    # Создаём временный файл
    tmp_dir = tempfile.mkdtemp(prefix="tgbot_voice_")
    local_path = os.path.join(tmp_dir, f"voice_{uid}.ogg")

    await bot.download_file(file.file_path, local_path)

    # Транскрибируем
    status_msg = await message.answer("🎤 Распознаю голос...")

    text = await transcribe_voice(local_path)

    # Чистим временный файл
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
        await message.answer("❌ Не удалось распознать голосовое сообщение. Попробуйте ещё раз или напишите текстом.")
        return

    # Показываем распознанный текст
    try:
        await status_msg.edit_text(f"🎤 Распознано: _{text}_\n\n⏳ Обрабатываю...", parse_mode="Markdown")
    except Exception:
        try:
            await status_msg.edit_text(f"🎤 Распознано: {text}\n\n⏳ Обрабатываю...")
        except Exception:
            pass

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

    # Сохраняем и отправляем в LLM
    save_message(uid, "user", text, agent_id)
    history = get_history(uid, agent_id, MAX_HISTORY_LENGTH)
    messages = [{"role": m["role"], "content": m["content"]} for m in history]

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

    # Удаляем статус
    try:
        await status_msg.delete()
    except Exception:
        pass

    if got_error:
        await message.answer(final_content, reply_markup=reply_kb)
        return

    # Отправляем ответ
    parts = split_text(final_content)
    for i, part in enumerate(parts):
        kb = reply_kb if i == len(parts) - 1 else None
        try:
            await message.answer(part, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await message.answer(part, reply_markup=kb)
