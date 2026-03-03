"""
Запланированные отчёты — пользователь настраивает периодические отчёты от агентов.
Используем APScheduler для cron-задач.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Глобальный scheduler (инициализируется при старте бота)
_scheduler = None
_bot = None


async def init_scheduler(bot):
    """Инициализация планировщика."""
    global _scheduler, _bot
    _bot = bot

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        _scheduler = AsyncIOScheduler()
        _scheduler.start()
        logger.info("Scheduler started")

        # Восстанавливаем сохранённые задачи из БД
        from db.scheduled import get_all_schedules
        schedules = get_all_schedules()
        for s in schedules:
            if s["active"]:
                _add_job(s)
        logger.info("Restored %d scheduled tasks", len([s for s in schedules if s["active"]]))

    except ImportError:
        logger.warning("APScheduler not installed. Scheduled reports disabled.")
        _scheduler = None


def _add_job(schedule: dict):
    """Добавляет задачу в планировщик."""
    if not _scheduler:
        return

    from apscheduler.triggers.cron import CronTrigger

    job_id = f"report_{schedule['id']}"

    # Удаляем старую задачу если есть
    try:
        _scheduler.remove_job(job_id)
    except Exception:
        pass

    # Парсим расписание (формат: HH:MM или cron-выражение)
    cron_expr = schedule.get("cron_expr", "0 9 * * *")
    parts = cron_expr.split()

    if len(parts) == 5:
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )
    elif len(parts) == 2:
        # Простой формат HH:MM
        trigger = CronTrigger(hour=parts[0], minute=parts[1])
    else:
        trigger = CronTrigger(hour=9, minute=0)  # По умолчанию 9:00

    _scheduler.add_job(
        _execute_report,
        trigger=trigger,
        id=job_id,
        args=[schedule],
        replace_existing=True,
    )
    logger.info("Added scheduled job: %s", job_id)


async def _execute_report(schedule: dict):
    """Выполняет запланированный отчёт."""
    if not _bot:
        logger.error("Bot not initialized for scheduled report")
        return

    try:
        from db.agents import get_agent
        from services.llm import chat_completion

        agent = get_agent(schedule["agent_id"])
        if not agent:
            logger.error("Agent %d not found for schedule %d", schedule["agent_id"], schedule["id"])
            return

        prompt = schedule.get("prompt", "Подготовь ежедневный отчёт.")
        user_id = schedule["user_id"]

        # Генерируем отчёт
        messages = [{"role": "user", "content": prompt}]
        result = await chat_completion(
            messages=messages,
            system_prompt=agent.get("system_prompt", ""),
        )

        report_text = (
            f"📋 **Запланированный отчёт**\n"
            f"🤖 Агент: {agent['emoji']} {agent['name']}\n"
            f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"{'─' * 30}\n\n"
            f"{result['content']}"
        )

        from services.text_utils import split_text
        parts = split_text(report_text)
        for part in parts:
            try:
                await _bot.send_message(user_id, part, parse_mode="Markdown")
            except Exception:
                await _bot.send_message(user_id, part)

        # Обновляем last_run
        from db.scheduled import update_last_run
        update_last_run(schedule["id"])

        logger.info("Scheduled report %d sent to user %d", schedule["id"], user_id)

    except Exception as e:
        logger.error("Scheduled report error: %s", e)


def add_schedule(schedule: dict):
    """Добавляет новое расписание."""
    _add_job(schedule)


def remove_schedule(schedule_id: int):
    """Удаляет расписание."""
    if not _scheduler:
        return
    try:
        _scheduler.remove_job(f"report_{schedule_id}")
    except Exception:
        pass


def stop_scheduler():
    """Останавливает планировщик."""
    if _scheduler:
        _scheduler.shutdown(wait=False)
