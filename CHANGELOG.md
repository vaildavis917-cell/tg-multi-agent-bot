# Changelog

## [2.0.0] — 2026-03-03

### Added

- **Web Search** — added DuckDuckGo-based web search for agents; results are injected into the agent's context for informed responses (`services/web_search.py`, `handlers/web_search.py`)
- **Multi-Agent Dialog** — added multi-agent discussion mode where 2–4 agents discuss a topic in turns, with a final summary (`handlers/multi_agent.py`)
- **Agent Comparison** — added side-by-side comparison mode that sends the same question to two agents and displays both answers (`handlers/multi_agent.py`)
- **Scheduled Reports** — added APScheduler-based scheduled reports; users can set up daily/weekly/custom cron reports from any agent (`services/scheduler.py`, `handlers/scheduled.py`, `db/scheduled.py`)
- **Agent Memory** — added long-term memory that extracts and stores key facts from conversations across sessions (`services/memory.py`, `handlers/memory.py`, `db/memory.py`)
- **Chart Generation** — added matplotlib-based chart generation; users describe a chart in natural language and the agent generates a Python script to create it (`services/charts.py`, `handlers/charts.py`)
- **Knowledge Base (RAG)** — added document upload and TF-IDF-based semantic search; users can build a personal knowledge base that agents reference during conversations (`services/rag.py`, `handlers/knowledge.py`, `db/knowledge.py`)
- **Market Data APIs** — added real-time market data from three sources:
  - Yahoo Finance (stocks, ETFs, indices — quotes, history, financials)
  - CoinGecko (cryptocurrency prices, top-10 rankings)
  - Alpha Vantage (Forex rates, technical indicators: RSI, MACD, SMA, etc.)
  - Interactive charts for stock price history (`services/market_data.py`, `handlers/market.py`)

### Changed

- Updated `bot.py` — integrated all 7 new routers with correct ordering (FSM routers before catch-all)
- Updated `keyboards/main_menu.py` — added 6 new menu buttons (Multi-Agent, Compare, Markets, Charts, Knowledge Base, Memory, Scheduled Reports)
- Updated `keyboards/agents_kb.py` — added Web Search button to agent panel
- Updated `config.py` — added `ALPHA_VANTAGE_KEY` configuration
- Updated `requirements.txt` — added `apscheduler`, `yfinance`, `matplotlib`, `numpy`
- Updated `db/__init__.py` — registered new database modules

## [1.0.0] — 2026-02-28

### Added

- Initial release with multi-agent Telegram bot
- Agent selection, favorites, templates, export
- Free chat mode with LLM
- Voice messages and file upload support
- Admin panel with whitelist, agent management, statistics
- Streaming responses via OpenRouter API
