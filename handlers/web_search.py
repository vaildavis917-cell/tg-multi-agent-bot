"""
Хендлер веб-поиска для агентов.
Пользователь нажимает кнопку 🔍 Поиск → вводит запрос → результаты добавляются в контекст.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.state import get_user_state
from db.history import save_message
from services.web_search import web_search, format_search_results
from keyboards.common_kb import cancel_kb

logger = logging.getLogger(__name__)
router = Router()


class SearchStates(StatesGroup):
    waiting_query = State()


@router.callback_query(F.data.startswith("search:agent:"))
async def on_search_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска — запрашиваем запрос."""
    agent_id = int(callback.data.split(":")[2])
    await state.set_state(SearchStates.waiting_query)
    await state.update_data(search_agent_id=agent_id)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "🔍 Введите поисковый запрос:\n\n"
        "Я найду актуальную информацию в интернете "
        "и добавлю её в контекст агента.",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(SearchStates.waiting_query)
async def on_search_query(message: Message, state: FSMContext):
    """Получен поисковый запрос — ищем и добавляем в контекст."""
    data = await state.get_data()
    agent_id = data.get("search_agent_id")
    await state.clear()

    uid = message.from_user.id
    query = message.text.strip()

    if not query:
        await message.answer("❌ Пустой запрос. Попробуйте ещё раз.")
        return

    status_msg = await message.answer("🔍 Ищу в интернете...")

    results = await web_search(query, max_results=5)
    formatted = format_search_results(results)

    # Сохраняем результаты поиска в историю как системное сообщение
    context_msg = (
        f"[РЕЗУЛЬТАТЫ ВЕБ-ПОИСКА по запросу: \"{query}\"]\n\n"
        f"{formatted}\n\n"
        f"[КОНЕЦ РЕЗУЛЬТАТОВ ПОИСКА. Используй эти данные для ответа пользователю.]"
    )
    save_message(uid, "user", context_msg, agent_id)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if results:
        preview = f"✅ Найдено {len(results)} результатов по запросу «{query}».\n\n"
        preview += "Результаты добавлены в контекст агента. Теперь задайте вопрос — агент учтёт найденную информацию."
    else:
        preview = f"⚠️ По запросу «{query}» ничего не найдено. Попробуйте другой запрос."

    await message.answer(preview)
