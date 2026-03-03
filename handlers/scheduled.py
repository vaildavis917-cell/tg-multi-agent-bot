"""
Хендлер для управления запланированными отчётами.
Пользователь может создать, просмотреть, включить/выключить, удалить расписание.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.agents import get_agents, get_agent
from db.scheduled import (
    add_schedule, get_user_schedules, get_schedule,
    toggle_schedule, delete_schedule,
)
from services.scheduler import add_schedule as scheduler_add, remove_schedule as scheduler_remove
from keyboards.common_kb import cancel_kb

logger = logging.getLogger(__name__)
router = Router()


class ScheduleStates(StatesGroup):
    selecting_agent = State()
    entering_prompt = State()
    entering_time = State()


# ═══════════════════════════════════════════════════════════
#  Список расписаний
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:scheduled")
async def on_scheduled_menu(callback: CallbackQuery):
    """Показывает список запланированных отчётов."""
    uid = callback.from_user.id
    schedules = get_user_schedules(uid)

    if not schedules:
        text = (
            "📋 **Запланированные отчёты**\n\n"
            "У вас пока нет запланированных отчётов.\n"
            "Создайте первый — агент будет автоматически "
            "отправлять вам отчёты по расписанию!"
        )
    else:
        text = "📋 **Запланированные отчёты**\n\n"
        for s in schedules:
            agent = get_agent(s["agent_id"])
            status = "🟢" if s["active"] else "🔴"
            agent_name = f"{agent['emoji']} {agent['name']}" if agent else "?"
            text += (
                f"{status} #{s['id']} — {agent_name}\n"
                f"   ⏰ {s['cron_expr']} | 📝 {s['prompt'][:50]}...\n\n"
            )

    buttons = [[InlineKeyboardButton(text="➕ Новый отчёт", callback_data="sched:new")]]

    for s in schedules:
        row = [
            InlineKeyboardButton(
                text=f"{'⏸' if s['active'] else '▶️'} #{s['id']}",
                callback_data=f"sched:toggle:{s['id']}",
            ),
            InlineKeyboardButton(
                text=f"🗑 #{s['id']}",
                callback_data=f"sched:delete:{s['id']}",
            ),
        ]
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  Создание нового расписания
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "sched:new")
async def on_sched_new(callback: CallbackQuery, state: FSMContext):
    """Начало создания — выбор агента."""
    agents = get_agents(active_only=True)
    buttons = [
        [InlineKeyboardButton(
            text=f"{a['emoji']} {a['name']}",
            callback_data=f"sched:agent:{a['id']}",
        )]
        for a in agents
    ]
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="menu:scheduled")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await state.set_state(ScheduleStates.selecting_agent)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "📋 Выберите агента для отчёта:",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sched:agent:"), ScheduleStates.selecting_agent)
async def on_sched_agent(callback: CallbackQuery, state: FSMContext):
    """Агент выбран — запрашиваем промпт."""
    agent_id = int(callback.data.split(":")[2])
    await state.update_data(sched_agent_id=agent_id)
    await state.set_state(ScheduleStates.entering_prompt)

    agent = get_agent(agent_id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        f"🤖 Агент: {agent['emoji']} {agent['name']}\n\n"
        "📝 Введите задание для отчёта.\n"
        "Например: «Подготовь обзор рынка S&P 500 за последний день»",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(ScheduleStates.entering_prompt)
async def on_sched_prompt(message: Message, state: FSMContext):
    """Промпт получен — запрашиваем время."""
    prompt = message.text.strip()
    if not prompt:
        await message.answer("❌ Пустое задание. Попробуйте ещё раз.")
        return

    await state.update_data(sched_prompt=prompt)
    await state.set_state(ScheduleStates.entering_time)

    await message.answer(
        "⏰ Введите время отправки отчёта.\n\n"
        "Форматы:\n"
        "• `09:00` — каждый день в 9:00\n"
        "• `0 9 * * 1-5` — по будням в 9:00\n"
        "• `0 18 * * 5` — каждую пятницу в 18:00\n\n"
        "По умолчанию: каждый день в 9:00",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )


@router.message(ScheduleStates.entering_time)
async def on_sched_time(message: Message, state: FSMContext):
    """Время получено — создаём расписание."""
    data = await state.get_data()
    agent_id = data["sched_agent_id"]
    prompt = data["sched_prompt"]
    await state.clear()

    uid = message.from_user.id
    time_input = message.text.strip()

    # Парсим время
    if ":" in time_input and len(time_input) <= 5:
        # Формат HH:MM
        parts = time_input.split(":")
        cron_expr = f"{parts[1]} {parts[0]} * * *"
    elif time_input:
        cron_expr = time_input
    else:
        cron_expr = "0 9 * * *"

    # Сохраняем в БД
    schedule_id = add_schedule(uid, agent_id, prompt, cron_expr)

    # Добавляем в планировщик
    schedule = get_schedule(schedule_id)
    if schedule:
        scheduler_add(schedule)

    agent = get_agent(agent_id)
    await message.answer(
        f"✅ Отчёт запланирован!\n\n"
        f"🤖 Агент: {agent['emoji']} {agent['name']}\n"
        f"📝 Задание: {prompt[:100]}\n"
        f"⏰ Расписание: {cron_expr}\n\n"
        f"Управление: /scheduled",
    )


# ═══════════════════════════════════════════════════════════
#  Управление расписаниями
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("sched:toggle:"))
async def on_sched_toggle(callback: CallbackQuery):
    """Включить/выключить расписание."""
    schedule_id = int(callback.data.split(":")[2])
    schedule = get_schedule(schedule_id)

    if not schedule or schedule["user_id"] != callback.from_user.id:
        await callback.answer("Расписание не найдено", show_alert=True)
        return

    new_state = toggle_schedule(schedule_id)

    if new_state:
        scheduler_add(get_schedule(schedule_id))
        await callback.answer("✅ Отчёт включён")
    else:
        scheduler_remove(schedule_id)
        await callback.answer("⏸ Отчёт приостановлен")

    # Обновляем список
    await on_scheduled_menu(callback)


@router.callback_query(F.data.startswith("sched:delete:"))
async def on_sched_delete(callback: CallbackQuery):
    """Удалить расписание."""
    schedule_id = int(callback.data.split(":")[2])
    schedule = get_schedule(schedule_id)

    if not schedule or schedule["user_id"] != callback.from_user.id:
        await callback.answer("Расписание не найдено", show_alert=True)
        return

    scheduler_remove(schedule_id)
    delete_schedule(schedule_id)

    await callback.answer("🗑 Отчёт удалён")
    await on_scheduled_menu(callback)
