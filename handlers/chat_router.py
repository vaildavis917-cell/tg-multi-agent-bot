"""
Роутер текстовых сообщений.
Определяет текущий режим пользователя и направляет в нужный обработчик.
"""

import logging
from aiogram import Router
from aiogram.types import Message

from config import MAX_HISTORY_LENGTH, MAX_MESSAGE_LENGTH
from db.state import get_user_state, set_user_state
from db.agents import get_agent
from db.history import get_history, save_message
from db.stats import log_usage
from services.llm import chat_completion
from services.text_utils import split_text
from keyboards import get_menu_kb, agent_selected_kb, free_chat_kb

logger = logging.getLogger(__name__)
router = Router()

FREE_CHAT_PROMPT = (
    "Ты — универсальный AI-ассистент Claude. "
    "Отвечай подробно, точно и полезно. "
    "Используй русский язык, если пользователь пишет на русском."
)


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
        await _process_llm(message, uid, agent_id, agent["system_prompt"], agent_selected_kb(agent_id))
        return

    # ── Свободный чат ────────────────────────────────────
    if mode == "free_chat":
        await _process_llm(message, uid, None, FREE_CHAT_PROMPT, free_chat_kb())
        return

    # ── Меню / неизвестный режим → подсказка ─────────────
    await message.answer(
        "Выберите режим через меню 👇",
        reply_markup=get_menu_kb(uid),
    )


async def _process_llm(message: Message, uid: int, agent_id, system_prompt: str, reply_kb):
    """Общая логика отправки в LLM и ответа пользователю."""
    save_message(uid, "user", message.text, agent_id)

    history = get_history(uid, agent_id, MAX_HISTORY_LENGTH)
    messages = [{"role": m["role"], "content": m["content"]} for m in history]

    typing_msg = await message.answer("⏳ Думаю...")

    result = await chat_completion(messages=messages, system_prompt=system_prompt)
    text = result["content"]

    save_message(uid, "assistant", text, agent_id)
    log_usage(uid, agent_id, result["tokens_in"], result["tokens_out"])

    try:
        await typing_msg.delete()
    except Exception:
        pass

    parts = split_text(text)
    for i, part in enumerate(parts):
        kb = reply_kb if i == len(parts) - 1 else None
        await message.answer(part, reply_markup=kb)
