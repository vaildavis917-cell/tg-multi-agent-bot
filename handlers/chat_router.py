"""
Роутер текстовых сообщений.
Определяет текущий режим пользователя и направляет в нужный обработчик.
Использует streaming для отображения ответа в реальном времени.
"""

import asyncio
import logging
from aiogram import Router
from aiogram.types import Message

from config import MAX_HISTORY_LENGTH, MAX_MESSAGE_LENGTH
from db.state import get_user_state, set_user_state
from db.agents import get_agent
from db.history import get_history, save_message
from db.stats import log_usage
from db.favorites import is_favorite
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

# Минимальный интервал между edit_message (Telegram rate limit)
STREAM_EDIT_INTERVAL = 1.5  # секунд
# Минимальное кол-во новых символов для обновления
STREAM_MIN_CHARS = 80


@router.message()
async def on_text_message(message: Message, **kwargs):
    """Обрабатывает все текстовые сообщения, которые не поймали другие хендлеры."""
    if not message.text:
        return

    uid = message.from_user.id
    state = get_user_state(uid)
    mode = state["current_mode"]

    # ── Режим агента ─────────────────────────────────────
    if mode == "agent":
        agent_id = state.get("current_agent_id")
        agent = get_agent(agent_id) if agent_id else None
        if not agent:
            set_user_state(uid, "menu")
            await message.answer("❌ Агент не найден. Возвращаю в меню.", reply_markup=get_menu_kb(uid))
            return
        fav = is_favorite(uid, agent_id)
        await _process_llm_stream(message, uid, agent_id, agent["system_prompt"], agent_selected_kb(agent_id, is_fav=fav))
        return

    # ── Свободный чат ────────────────────────────────────
    if mode == "free_chat":
        await _process_llm_stream(message, uid, None, FREE_CHAT_PROMPT, free_chat_kb())
        return

    # ── Меню / неизвестный режим → подсказка ─────────────
    await message.answer(
        "Выберите режим через меню 👇",
        reply_markup=get_menu_kb(uid),
    )


async def _process_llm_stream(message: Message, uid: int, agent_id, system_prompt: str, reply_kb):
    """Streaming-обработка: сообщение обновляется в реальном времени."""
    save_message(uid, "user", message.text, agent_id)

    history = get_history(uid, agent_id, MAX_HISTORY_LENGTH)
    messages = [{"role": m["role"], "content": m["content"]} for m in history]

    # Отправляем начальное сообщение
    typing_msg = await message.answer("⏳ Думаю...")

    last_edit_time = 0.0
    last_edit_len = 0
    final_content = ""
    got_error = False

    async for event in chat_completion_stream(messages=messages, system_prompt=system_prompt):
        etype = event["type"]

        if etype == "error":
            final_content = event["content"]
            got_error = True
            break

        if etype == "chunk":
            current_text = event["content"]
            now = asyncio.get_event_loop().time()

            # Обновляем сообщение если прошло достаточно времени и текст вырос
            if (now - last_edit_time >= STREAM_EDIT_INTERVAL
                    and len(current_text) - last_edit_len >= STREAM_MIN_CHARS):
                display = current_text[:MAX_MESSAGE_LENGTH - 3]
                if len(current_text) > MAX_MESSAGE_LENGTH - 3:
                    display += "..."
                display += "\n\n⏳ _Генерирую..._"
                try:
                    await typing_msg.edit_text(display, parse_mode="Markdown")
                except Exception:
                    try:
                        await typing_msg.edit_text(display)
                    except Exception:
                        pass
                last_edit_time = now
                last_edit_len = len(current_text)

        if etype == "done":
            final_content = event["content"]
            tokens_in = event.get("tokens_in", 0)
            tokens_out = event.get("tokens_out", 0)
            save_message(uid, "assistant", final_content, agent_id)
            log_usage(uid, agent_id, tokens_in, tokens_out)
            break

    # Удаляем typing-сообщение
    try:
        await typing_msg.delete()
    except Exception:
        pass

    if got_error:
        await message.answer(final_content, reply_markup=reply_kb)
        return

    # Отправляем финальный ответ (может быть длинным — разбиваем)
    parts = split_text(final_content)
    for i, part in enumerate(parts):
        kb = reply_kb if i == len(parts) - 1 else None
        try:
            await message.answer(part, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await message.answer(part, reply_markup=kb)
