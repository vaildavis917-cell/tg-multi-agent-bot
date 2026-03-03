"""
Хендлер для рыночных данных — котировки, крипта, форекс.
"""

import logging
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.market_data import (
    get_stock_quote, get_stock_history,
    get_crypto_price, get_top_cryptos,
    get_forex_rate, get_technical_indicator,
    format_stock_quote, format_crypto_price,
    format_forex_rate, format_top_cryptos,
)
from services.charts import generate_chart_from_data
from keyboards.common_kb import cancel_kb

logger = logging.getLogger(__name__)
router = Router()


class MarketStates(StatesGroup):
    waiting_stock = State()
    waiting_crypto = State()
    waiting_forex = State()


# ═══════════════════════════════════════════════════════════
#  Главное меню рынков
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:market")
async def on_market_menu(callback: CallbackQuery):
    """Меню рыночных данных."""
    buttons = [
        [InlineKeyboardButton(text="📈 Акции / ETF / Индексы", callback_data="market:stock")],
        [InlineKeyboardButton(text="🪙 Криптовалюты", callback_data="market:crypto")],
        [InlineKeyboardButton(text="💱 Форекс (валюты)", callback_data="market:forex")],
        [InlineKeyboardButton(text="🏆 Топ-10 крипто", callback_data="market:top_crypto")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "📊 **Рыночные данные**\n\n"
        "Реальные котировки акций, криптовалют и валют.\n"
        "Выберите раздел:",
        reply_markup=kb,
        parse_mode="Markdown",
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  Акции
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "market:stock")
async def on_stock(callback: CallbackQuery, state: FSMContext):
    """Запрос тикера акции."""
    await state.set_state(MarketStates.waiting_stock)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "📈 Введите тикер акции/ETF/индекса:\n\n"
        "Примеры: `AAPL`, `MSFT`, `TSLA`, `SPY`, `^GSPC`, `SBER.ME`",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(MarketStates.waiting_stock)
async def on_stock_ticker(message: Message, state: FSMContext):
    """Получен тикер — показываем котировку."""
    await state.clear()
    symbol = message.text.strip().upper()

    status_msg = await message.answer(f"📈 Загружаю данные по {symbol}...")

    quote = await get_stock_quote(symbol)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if not quote:
        await message.answer(
            f"❌ Тикер `{symbol}` не найден.\n"
            "Проверьте правильность написания.",
            parse_mode="Markdown",
        )
        return

    text = format_stock_quote(quote)

    buttons = [
        [InlineKeyboardButton(text="📊 График 1 мес", callback_data=f"chart:stock:{symbol}:1mo")],
        [InlineKeyboardButton(text="📊 График 1 год", callback_data=f"chart:stock:{symbol}:1y")],
        [InlineKeyboardButton(text="📈 Ещё тикер", callback_data="market:stock")],
        [InlineKeyboardButton(text="◀️ Рынки", callback_data="menu:market")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("chart:stock:"))
async def on_stock_chart(callback: CallbackQuery):
    """Генерирует график акции."""
    parts = callback.data.split(":")
    symbol = parts[2]
    period = parts[3]

    status_msg = await callback.message.answer(f"📊 Строю график {symbol} ({period})...")

    history = await get_stock_history(symbol, period)

    if not history:
        await status_msg.edit_text("❌ Не удалось получить исторические данные.")
        await callback.answer()
        return

    # Генерируем график
    data = {
        "dates": [h["date"] for h in history],
        "close": [h["close"] for h in history],
    }

    chart_path = await generate_chart_from_data(
        data=data,
        chart_type="line",
        title=f"{symbol} — {period}",
        chart_id=f"stock_{symbol}_{period}",
    )

    try:
        await status_msg.delete()
    except Exception:
        pass

    if chart_path:
        import os
        photo = FSInputFile(chart_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"📊 {symbol} за {period}",
        )
        try:
            os.remove(chart_path)
        except Exception:
            pass
    else:
        # Fallback — текстовые данные
        text = f"📊 **{symbol}** за {period}:\n\n"
        for h in history[-10:]:
            text += f"{h['date']}: ${h['close']}\n"
        await callback.message.answer(text, parse_mode="Markdown")

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  Криптовалюты
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "market:crypto")
async def on_crypto(callback: CallbackQuery, state: FSMContext):
    """Запрос криптовалюты."""
    await state.set_state(MarketStates.waiting_crypto)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "🪙 Введите название криптовалюты:\n\n"
        "Примеры: `bitcoin`, `ethereum`, `solana`, `dogecoin`, `ripple`",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(MarketStates.waiting_crypto)
async def on_crypto_name(message: Message, state: FSMContext):
    """Получена крипта — показываем цену."""
    await state.clear()
    coin = message.text.strip().lower()

    status_msg = await message.answer(f"🪙 Загружаю данные по {coin}...")

    data = await get_crypto_price(coin)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if not data:
        await message.answer(
            f"❌ Криптовалюта `{coin}` не найдена.\n"
            "Используйте полное название: bitcoin, ethereum, solana...",
            parse_mode="Markdown",
        )
        return

    text = format_crypto_price(data)

    buttons = [
        [InlineKeyboardButton(text="🪙 Ещё крипта", callback_data="market:crypto")],
        [InlineKeyboardButton(text="🏆 Топ-10", callback_data="market:top_crypto")],
        [InlineKeyboardButton(text="◀️ Рынки", callback_data="menu:market")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "market:top_crypto")
async def on_top_crypto(callback: CallbackQuery):
    """Топ-10 криптовалют."""
    status_msg = await callback.message.answer("🏆 Загружаю топ криптовалют...")

    data = await get_top_cryptos(10)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if not data:
        await callback.message.answer("❌ Не удалось загрузить данные.")
        await callback.answer()
        return

    text = format_top_cryptos(data)

    buttons = [
        [InlineKeyboardButton(text="🪙 Подробнее о монете", callback_data="market:crypto")],
        [InlineKeyboardButton(text="◀️ Рынки", callback_data="menu:market")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await callback.message.answer(text, reply_markup=kb)

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  Форекс
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "market:forex")
async def on_forex(callback: CallbackQuery, state: FSMContext):
    """Запрос валютной пары."""
    await state.set_state(MarketStates.waiting_forex)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "💱 Введите валютную пару (через /):\n\n"
        "Примеры: `USD/RUB`, `EUR/USD`, `GBP/JPY`, `BTC/USD`",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(MarketStates.waiting_forex)
async def on_forex_pair(message: Message, state: FSMContext):
    """Получена пара — показываем курс."""
    await state.clear()
    text_input = message.text.strip().upper()

    # Парсим пару
    if "/" in text_input:
        parts = text_input.split("/")
        from_cur, to_cur = parts[0].strip(), parts[1].strip()
    elif len(text_input) == 6:
        from_cur, to_cur = text_input[:3], text_input[3:]
    else:
        await message.answer("❌ Неверный формат. Используйте: USD/RUB")
        return

    status_msg = await message.answer(f"💱 Загружаю курс {from_cur}/{to_cur}...")

    data = await get_forex_rate(from_cur, to_cur)

    try:
        await status_msg.delete()
    except Exception:
        pass

    if not data:
        await message.answer(f"❌ Не удалось получить курс {from_cur}/{to_cur}.")
        return

    text = format_forex_rate(data)

    buttons = [
        [InlineKeyboardButton(text="💱 Ещё пара", callback_data="market:forex")],
        [InlineKeyboardButton(text="◀️ Рынки", callback_data="menu:market")],
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await message.answer(text, reply_markup=kb)
