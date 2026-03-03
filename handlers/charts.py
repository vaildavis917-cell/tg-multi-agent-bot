"""
Хендлер для генерации графиков.
Пользователь описывает график → агент генерирует визуализацию.
"""

import os
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.charts import generate_chart
from keyboards.common_kb import cancel_kb

logger = logging.getLogger(__name__)
router = Router()

_chart_counter = 0


class ChartStates(StatesGroup):
    waiting_description = State()


@router.callback_query(F.data == "menu:charts")
async def on_charts_menu(callback: CallbackQuery, state: FSMContext):
    """Начало генерации графика."""
    await state.set_state(ChartStates.waiting_description)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "📊 **Генерация графиков**\n\n"
        "Опишите, какой график вы хотите получить.\n\n"
        "Примеры:\n"
        "• «Линейный график роста S&P 500 за 2024 год»\n"
        "• «Круговая диаграмма распределения портфеля: акции 60%, облигации 25%, кэш 15%»\n"
        "• «Сравнение доходности Apple, Google, Microsoft за 5 лет»\n"
        "• «Гистограмма ВВП топ-10 стран мира»\n\n"
        "📝 Введите описание:",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ChartStates.waiting_description)
async def on_chart_description(message: Message, state: FSMContext):
    """Получено описание — генерируем график."""
    await state.clear()

    description = message.text.strip()
    if not description:
        await message.answer("❌ Пустое описание.")
        return

    global _chart_counter
    _chart_counter += 1
    chart_id = f"user_{message.from_user.id}_{_chart_counter}"

    status_msg = await message.answer("📊 Генерирую график... Это может занять 10-20 секунд.")

    chart_path = await generate_chart(description, chart_id)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if chart_path and os.path.exists(chart_path):
        photo = FSInputFile(chart_path)
        buttons = [
            [InlineKeyboardButton(text="📊 Ещё график", callback_data="menu:charts")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data="menu:back")],
        ]
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer_photo(
            photo=photo,
            caption=f"📊 График: {description[:200]}",
            reply_markup=kb,
        )

        # Удаляем временный файл
        try:
            os.remove(chart_path)
        except Exception:
            pass
    else:
        await message.answer(
            "⚠️ Не удалось сгенерировать график.\n"
            "Попробуйте описать его более конкретно.\n\n"
            "Например: «Столбчатый график: Россия 2.1 трлн, Бразилия 1.9 трлн, Индия 3.7 трлн»",
        )
