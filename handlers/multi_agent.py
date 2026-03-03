"""
Мульти-агентный диалог и сравнение ответов.
Пользователь задаёт вопрос — несколько агентов отвечают по очереди.
Или сравнивает ответы двух агентов на один вопрос.
"""

import asyncio
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.agents import get_agents, get_agent
from services.llm import chat_completion
from services.text_utils import split_text
from keyboards.common_kb import cancel_kb

logger = logging.getLogger(__name__)
router = Router()

# Максимум агентов в мульти-режиме
MAX_MULTI_AGENTS = 4


class MultiAgentStates(StatesGroup):
    selecting_agents = State()
    waiting_question = State()


class CompareStates(StatesGroup):
    selecting_first = State()
    selecting_second = State()
    waiting_question = State()


# ═══════════════════════════════════════════════════════════
#  Мульти-агентный диалог
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:multi_agent")
async def on_multi_agent(callback: CallbackQuery, state: FSMContext):
    """Начало мульти-агентного диалога — выбор агентов."""
    agents = get_agents(active_only=True)
    if not agents:
        await callback.answer("Нет доступных агентов", show_alert=True)
        return

    await state.set_state(MultiAgentStates.selecting_agents)
    await state.update_data(selected_agents=[])

    kb = _multi_select_kb(agents, [])

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "🤖 **Мульти-агентный диалог**\n\n"
        f"Выберите до {MAX_MULTI_AGENTS} агентов, которые будут отвечать на ваш вопрос.\n"
        "Нажмите на агента чтобы выбрать/убрать, затем «Готово».",
        reply_markup=kb,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("multi:toggle:"), MultiAgentStates.selecting_agents)
async def on_multi_toggle(callback: CallbackQuery, state: FSMContext):
    """Переключение выбора агента."""
    agent_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    selected = data.get("selected_agents", [])

    if agent_id in selected:
        selected.remove(agent_id)
    else:
        if len(selected) >= MAX_MULTI_AGENTS:
            await callback.answer(f"Максимум {MAX_MULTI_AGENTS} агента!", show_alert=True)
            return
        selected.append(agent_id)

    await state.update_data(selected_agents=selected)

    agents = get_agents(active_only=True)
    kb = _multi_select_kb(agents, selected)

    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "multi:done", MultiAgentStates.selecting_agents)
async def on_multi_done(callback: CallbackQuery, state: FSMContext):
    """Агенты выбраны — запрашиваем вопрос."""
    data = await state.get_data()
    selected = data.get("selected_agents", [])

    if len(selected) < 2:
        await callback.answer("Выберите минимум 2 агента!", show_alert=True)
        return

    await state.set_state(MultiAgentStates.waiting_question)

    agent_names = []
    for aid in selected:
        a = get_agent(aid)
        if a:
            agent_names.append(f"{a['emoji']} {a['name']}")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"✅ Выбрано {len(selected)} агентов:\n"
        + "\n".join(f"  • {n}" for n in agent_names)
        + "\n\n📝 Теперь введите ваш вопрос:",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(MultiAgentStates.waiting_question)
async def on_multi_question(message: Message, state: FSMContext):
    """Получен вопрос — отправляем всем агентам."""
    data = await state.get_data()
    selected = data.get("selected_agents", [])
    await state.clear()

    question = message.text.strip()
    if not question:
        await message.answer("❌ Пустой вопрос.")
        return

    status_msg = await message.answer(
        f"🔄 Отправляю вопрос {len(selected)} агентам...\n"
        "Это может занять некоторое время."
    )

    # Параллельные запросы ко всем агентам
    tasks = []
    for agent_id in selected:
        agent = get_agent(agent_id)
        if agent:
            tasks.append(_ask_agent(agent, question))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    try:
        await status_msg.delete()
    except Exception:
        pass

    # Отправляем ответы по очереди
    for i, (agent_id, result) in enumerate(zip(selected, results)):
        agent = get_agent(agent_id)
        if not agent:
            continue

        if isinstance(result, Exception):
            text = f"⚠️ Ошибка: {result}"
        else:
            text = result

        header = f"{'─' * 30}\n{agent['emoji']} **{agent['name']}**\n{'─' * 30}\n\n"
        full_text = header + text

        parts = split_text(full_text)
        for part in parts:
            try:
                await message.answer(part, parse_mode="Markdown")
            except Exception:
                await message.answer(part)

    # Финальное сообщение
    from keyboards import get_menu_kb
    await message.answer(
        "✅ Все агенты ответили!\n\n"
        "Можете задать новый вопрос или вернуться в меню.",
        reply_markup=get_menu_kb(message.from_user.id),
    )


# ═══════════════════════════════════════════════════════════
#  Сравнение двух агентов
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:compare")
async def on_compare_start(callback: CallbackQuery, state: FSMContext):
    """Начало сравнения — выбор первого агента."""
    agents = get_agents(active_only=True)
    if len(agents) < 2:
        await callback.answer("Нужно минимум 2 агента для сравнения", show_alert=True)
        return

    await state.set_state(CompareStates.selecting_first)
    kb = _agent_select_kb(agents, "cmp1")

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "⚖️ **Сравнение агентов**\n\n"
        "Выберите **первого** агента:",
        reply_markup=kb,
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cmp1:"), CompareStates.selecting_first)
async def on_compare_first(callback: CallbackQuery, state: FSMContext):
    """Первый агент выбран — выбираем второго."""
    first_id = int(callback.data.split(":")[1])
    await state.update_data(compare_first=first_id)
    await state.set_state(CompareStates.selecting_second)

    agents = [a for a in get_agents(active_only=True) if a["id"] != first_id]
    kb = _agent_select_kb(agents, "cmp2")

    first = get_agent(first_id)
    first_name = f"{first['emoji']} {first['name']}" if first else "?"

    try:
        await callback.message.edit_text(
            f"⚖️ Первый агент: {first_name}\n\n"
            "Выберите **второго** агента:",
            reply_markup=kb,
            parse_mode="Markdown",
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("cmp2:"), CompareStates.selecting_second)
async def on_compare_second(callback: CallbackQuery, state: FSMContext):
    """Второй агент выбран — запрашиваем вопрос."""
    second_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    first_id = data["compare_first"]
    await state.update_data(compare_second=second_id)
    await state.set_state(CompareStates.waiting_question)

    first = get_agent(first_id)
    second = get_agent(second_id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"⚖️ Сравнение:\n"
        f"  1️⃣ {first['emoji']} {first['name']}\n"
        f"  2️⃣ {second['emoji']} {second['name']}\n\n"
        f"📝 Введите вопрос для сравнения:",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(CompareStates.waiting_question)
async def on_compare_question(message: Message, state: FSMContext):
    """Получен вопрос — отправляем обоим агентам параллельно."""
    data = await state.get_data()
    first_id = data["compare_first"]
    second_id = data["compare_second"]
    await state.clear()

    question = message.text.strip()
    if not question:
        await message.answer("❌ Пустой вопрос.")
        return

    first = get_agent(first_id)
    second = get_agent(second_id)

    status_msg = await message.answer("⚖️ Сравниваю ответы двух агентов...")

    # Параллельные запросы
    r1, r2 = await asyncio.gather(
        _ask_agent(first, question),
        _ask_agent(second, question),
        return_exceptions=True,
    )

    try:
        await status_msg.delete()
    except Exception:
        pass

    # Ответ первого агента
    header1 = f"1️⃣ {first['emoji']} **{first['name']}**\n{'─' * 30}\n\n"
    text1 = header1 + (str(r1) if not isinstance(r1, Exception) else f"⚠️ Ошибка: {r1}")
    for part in split_text(text1):
        try:
            await message.answer(part, parse_mode="Markdown")
        except Exception:
            await message.answer(part)

    # Ответ второго агента
    header2 = f"\n2️⃣ {second['emoji']} **{second['name']}**\n{'─' * 30}\n\n"
    text2 = header2 + (str(r2) if not isinstance(r2, Exception) else f"⚠️ Ошибка: {r2}")
    for part in split_text(text2):
        try:
            await message.answer(part, parse_mode="Markdown")
        except Exception:
            await message.answer(part)

    from keyboards import get_menu_kb
    await message.answer(
        "✅ Сравнение завершено!",
        reply_markup=get_menu_kb(message.from_user.id),
    )


# ═══════════════════════════════════════════════════════════
#  Утилиты
# ═══════════════════════════════════════════════════════════

async def _ask_agent(agent: dict, question: str) -> str:
    """Отправляет вопрос агенту и возвращает ответ."""
    messages = [{"role": "user", "content": question}]
    result = await chat_completion(
        messages=messages,
        system_prompt=agent.get("system_prompt", ""),
    )
    return result["content"]


def _multi_select_kb(agents: list[dict], selected: list[int]) -> InlineKeyboardMarkup:
    """Клавиатура мульти-выбора агентов."""
    buttons = []
    for a in agents:
        check = "✅" if a["id"] in selected else "⬜"
        buttons.append([InlineKeyboardButton(
            text=f"{check} {a['emoji']} {a['name']}",
            callback_data=f"multi:toggle:{a['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="multi:done")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _agent_select_kb(agents: list[dict], prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора одного агента."""
    buttons = [
        [InlineKeyboardButton(
            text=f"{a['emoji']} {a['name']}",
            callback_data=f"{prefix}:{a['id']}",
        )]
        for a in agents
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
