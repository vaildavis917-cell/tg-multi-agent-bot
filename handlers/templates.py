"""
Хендлеры шаблонов быстрых запросов.
"""

import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from db.templates import get_templates, get_template
from db.state import get_user_state, set_user_state
from db.agents import get_agent
from db.history import save_message, get_history
from db.stats import log_usage
from config import MAX_HISTORY_LENGTH
from services.llm_stream import chat_completion_stream
from services.text_utils import split_text
from keyboards.templates_kb import templates_list_kb
from keyboards import agent_selected_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("agent:templates:"))
async def cb_show_templates(callback: CallbackQuery, **kwargs):
    """Показать шаблоны для агента."""
    agent_id = int(callback.data.split(":")[2])
    templates = get_templates(agent_id)

    if not templates:
        await callback.answer("📝 Для этого агента пока нет шаблонов.", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    agent = get_agent(agent_id)
    name = agent["name"] if agent else "Агент"

    await callback.message.answer(
        f"⚡ **Быстрые запросы для {name}:**\n\nВыберите шаблон:",
        parse_mode="Markdown",
        reply_markup=templates_list_kb(templates, agent_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tpl:use:"))
async def cb_use_template(callback: CallbackQuery, **kwargs):
    """Использовать шаблон — отправить его текст в LLM."""
    template_id = int(callback.data.split(":")[2])
    tpl = get_template(template_id)

    if not tpl:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return

    uid = callback.from_user.id
    agent_id = tpl["agent_id"]
    agent = get_agent(agent_id)

    if not agent:
        await callback.answer("❌ Агент не найден", show_alert=True)
        return

    # Устанавливаем состояние
    set_user_state(uid, "agent", agent_id)

    # Сохраняем как сообщение пользователя
    save_message(uid, "user", tpl["text"], agent_id)

    # Отправляем в LLM
    history = get_history(uid, agent_id, MAX_HISTORY_LENGTH)
    messages = [{"role": m["role"], "content": m["content"]} for m in history]

    try:
        await callback.message.delete()
    except Exception:
        pass

    typing_msg = await callback.message.answer(f"⚡ _{tpl['title']}_\n\n⏳ Обрабатываю...", parse_mode="Markdown")

    final_content = ""
    got_error = False

    async for event in chat_completion_stream(messages=messages, system_prompt=agent["system_prompt"]):
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
        await typing_msg.delete()
    except Exception:
        pass

    reply_kb = agent_selected_kb(agent_id)
    if got_error:
        await callback.message.answer(final_content, reply_markup=reply_kb)
        return

    parts = split_text(final_content)
    for i, part in enumerate(parts):
        kb = reply_kb if i == len(parts) - 1 else None
        try:
            await callback.message.answer(part, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            await callback.message.answer(part, reply_markup=kb)
