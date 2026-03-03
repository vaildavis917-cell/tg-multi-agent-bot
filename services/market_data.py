"""
API бирж — реальные рыночные данные для финансовых агентов.

Источники:
- Yahoo Finance (yfinance) — акции, ETF, индексы
- CoinGecko — криптовалюты
- Alpha Vantage — Forex, технические индикаторы
"""

import logging
import aiohttp
import json
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from config import ALPHA_VANTAGE_KEY
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"


# ═══════════════════════════════════════════════════════════
#  Yahoo Finance (через yfinance)
# ═══════════════════════════════════════════════════════════

async def get_stock_quote(symbol: str) -> Optional[dict]:
    """
    Получает котировку акции/ETF/индекса через yfinance.
    Возвращает: {symbol, name, price, change, change_pct, volume, market_cap, ...}
    """
    try:
        import yfinance as yf
        import asyncio

        def _fetch():
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if not info or "regularMarketPrice" not in info:
                # Пробуем fast_info
                fast = ticker.fast_info
                if hasattr(fast, 'last_price') and fast.last_price:
                    return {
                        "symbol": symbol.upper(),
                        "name": symbol.upper(),
                        "price": round(fast.last_price, 2),
                        "currency": getattr(fast, 'currency', 'USD'),
                        "market_cap": getattr(fast, 'market_cap', None),
                    }
                return None

            return {
                "symbol": symbol.upper(),
                "name": info.get("shortName", info.get("longName", symbol)),
                "price": info.get("regularMarketPrice") or info.get("currentPrice"),
                "prev_close": info.get("regularMarketPreviousClose"),
                "change": info.get("regularMarketChange"),
                "change_pct": info.get("regularMarketChangePercent"),
                "volume": info.get("regularMarketVolume"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
            }

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _fetch)
        return result

    except Exception as e:
        logger.error("Yahoo Finance error for %s: %s", symbol, e)
        return None


async def get_stock_history(symbol: str, period: str = "1mo") -> Optional[list[dict]]:
    """
    Получает историю котировок.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    """
    try:
        import yfinance as yf
        import asyncio

        def _fetch():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            if hist.empty:
                return None

            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"]),
                })
            return data

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)

    except Exception as e:
        logger.error("Yahoo Finance history error for %s: %s", symbol, e)
        return None


# ═══════════════════════════════════════════════════════════
#  CoinGecko — Криптовалюты
# ═══════════════════════════════════════════════════════════

async def get_crypto_price(coin_id: str) -> Optional[dict]:
    """
    Получает цену криптовалюты.
    coin_id: bitcoin, ethereum, solana, etc.
    """
    try:
        url = f"{COINGECKO_BASE}/simple/price"
        params = {
            "ids": coin_id.lower(),
            "vs_currencies": "usd,eur,rub",
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        if coin_id.lower() not in data:
            return None

        coin_data = data[coin_id.lower()]
        return {
            "coin": coin_id,
            "price_usd": coin_data.get("usd"),
            "price_eur": coin_data.get("eur"),
            "price_rub": coin_data.get("rub"),
            "change_24h": coin_data.get("usd_24h_change"),
            "market_cap_usd": coin_data.get("usd_market_cap"),
            "volume_24h_usd": coin_data.get("usd_24h_vol"),
        }

    except Exception as e:
        logger.error("CoinGecko error for %s: %s", coin_id, e)
        return None


async def get_top_cryptos(limit: int = 10) -> Optional[list[dict]]:
    """Получает топ криптовалют по капитализации."""
    try:
        url = f"{COINGECKO_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        return [
            {
                "rank": i + 1,
                "name": coin["name"],
                "symbol": coin["symbol"].upper(),
                "price_usd": coin["current_price"],
                "change_24h": coin.get("price_change_percentage_24h"),
                "market_cap": coin.get("market_cap"),
                "volume_24h": coin.get("total_volume"),
            }
            for i, coin in enumerate(data)
        ]

    except Exception as e:
        logger.error("CoinGecko top cryptos error: %s", e)
        return None


# ═══════════════════════════════════════════════════════════
#  Alpha Vantage — Forex + Технические индикаторы
# ═══════════════════════════════════════════════════════════

async def get_forex_rate(from_currency: str, to_currency: str) -> Optional[dict]:
    """Получает курс валютной пары."""
    if not ALPHA_VANTAGE_KEY:
        return None

    try:
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "apikey": ALPHA_VANTAGE_KEY,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                ALPHA_VANTAGE_BASE, params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        rate_data = data.get("Realtime Currency Exchange Rate", {})
        if not rate_data:
            return None

        return {
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "rate": float(rate_data.get("5. Exchange Rate", 0)),
            "bid": float(rate_data.get("8. Bid Price", 0)),
            "ask": float(rate_data.get("9. Ask Price", 0)),
            "last_updated": rate_data.get("6. Last Refreshed", ""),
        }

    except Exception as e:
        logger.error("Alpha Vantage forex error: %s", e)
        return None


async def get_technical_indicator(
    symbol: str,
    indicator: str = "RSI",
    interval: str = "daily",
    time_period: int = 14,
) -> Optional[dict]:
    """
    Получает технический индикатор.
    indicator: RSI, MACD, SMA, EMA, BBANDS, STOCH, ADX
    interval: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
    """
    if not ALPHA_VANTAGE_KEY:
        return None

    try:
        params = {
            "function": indicator.upper(),
            "symbol": symbol.upper(),
            "interval": interval,
            "time_period": time_period,
            "series_type": "close",
            "apikey": ALPHA_VANTAGE_KEY,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                ALPHA_VANTAGE_BASE, params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()

        # Извлекаем последние значения
        meta = data.get("Meta Data", {})
        # Ищем ключ с данными (формат: "Technical Analysis: RSI")
        data_key = None
        for key in data:
            if "Technical Analysis" in key:
                data_key = key
                break

        if not data_key or data_key not in data:
            return None

        values = data[data_key]
        # Берём последние 5 значений
        recent = list(values.items())[:5]

        return {
            "symbol": symbol.upper(),
            "indicator": indicator.upper(),
            "interval": interval,
            "values": [
                {"date": date, **{k: float(v) for k, v in vals.items()}}
                for date, vals in recent
            ],
        }

    except Exception as e:
        logger.error("Alpha Vantage indicator error: %s", e)
        return None


# ═══════════════════════════════════════════════════════════
#  Форматирование для контекста LLM
# ═══════════════════════════════════════════════════════════

def format_stock_quote(data: dict) -> str:
    """Форматирует котировку акции."""
    if not data:
        return "❌ Данные не найдены."

    lines = [f"📈 **{data['symbol']}** — {data.get('name', '')}"]
    lines.append(f"💰 Цена: **${data['price']}** {data.get('currency', '')}")

    if data.get("change") is not None:
        sign = "+" if data["change"] >= 0 else ""
        emoji = "🟢" if data["change"] >= 0 else "🔴"
        lines.append(f"{emoji} Изменение: {sign}{data['change']:.2f} ({sign}{data.get('change_pct', 0):.2f}%)")

    if data.get("volume"):
        lines.append(f"📊 Объём: {data['volume']:,}")
    if data.get("market_cap"):
        cap_b = data["market_cap"] / 1e9
        lines.append(f"🏢 Капитализация: ${cap_b:.1f}B")
    if data.get("pe_ratio"):
        lines.append(f"📐 P/E: {data['pe_ratio']:.1f}")
    if data.get("dividend_yield"):
        lines.append(f"💵 Дивиденды: {data['dividend_yield']*100:.2f}%")
    if data.get("52w_high"):
        lines.append(f"📈 52W High/Low: ${data['52w_high']:.2f} / ${data.get('52w_low', 0):.2f}")
    if data.get("sector"):
        lines.append(f"🏭 Сектор: {data['sector']}")

    return "\n".join(lines)


def format_crypto_price(data: dict) -> str:
    """Форматирует цену криптовалюты."""
    if not data:
        return "❌ Данные не найдены."

    lines = [f"🪙 **{data['coin'].upper()}**"]
    lines.append(f"💰 ${data['price_usd']:,.2f}")

    if data.get("price_rub"):
        lines.append(f"🇷🇺 ₽{data['price_rub']:,.0f}")

    if data.get("change_24h") is not None:
        sign = "+" if data["change_24h"] >= 0 else ""
        emoji = "🟢" if data["change_24h"] >= 0 else "🔴"
        lines.append(f"{emoji} 24ч: {sign}{data['change_24h']:.2f}%")

    if data.get("market_cap_usd"):
        cap_b = data["market_cap_usd"] / 1e9
        lines.append(f"🏢 MCap: ${cap_b:.1f}B")

    return "\n".join(lines)


def format_forex_rate(data: dict) -> str:
    """Форматирует курс валюты."""
    if not data:
        return "❌ Данные не найдены."

    return (
        f"💱 **{data['from']}/{data['to']}**\n"
        f"💰 Курс: {data['rate']:.4f}\n"
        f"📊 Bid/Ask: {data['bid']:.4f} / {data['ask']:.4f}\n"
        f"🕐 Обновлено: {data['last_updated']}"
    )


def format_top_cryptos(data: list[dict]) -> str:
    """Форматирует топ криптовалют."""
    if not data:
        return "❌ Данные не найдены."

    lines = ["🏆 **Топ криптовалют по капитализации:**\n"]
    for coin in data:
        change = coin.get("change_24h", 0)
        sign = "+" if change and change >= 0 else ""
        emoji = "🟢" if change and change >= 0 else "🔴"
        cap_b = coin.get("market_cap", 0) / 1e9 if coin.get("market_cap") else 0

        lines.append(
            f"{coin['rank']}. **{coin['symbol']}** — ${coin['price_usd']:,.2f} "
            f"{emoji} {sign}{change:.1f}% | MCap: ${cap_b:.0f}B"
        )

    return "\n".join(lines)
