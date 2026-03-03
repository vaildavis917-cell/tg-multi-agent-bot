# Multi-Agent Telegram Bot (Claude Opus 4.6)

Мульти-агентный Telegram бот на базе Claude Opus 4.6 через OpenRouter API. Бот предоставляет доступ к 8 специализированным финансовым AI-агентам, режиму свободного чата, рыночным данным в реальном времени и продвинутым инструментам анализа.

## Возможности

### Агенты и чат
- **8 финансовых агентов** — каждый со своим системным промптом и ролью (Goldman Sachs, Morgan Stanley, Bridgewater, JPMorgan, BlackRock, Citadel, Harvard Endowment, Bain & Company)
- **Свободный чат** — прямое общение с Claude Opus 4.6 без ограничений
- **Мульти-агентный диалог** — 2–4 агента обсуждают тему по очереди с итоговым резюме
- **Сравнение ответов** — один вопрос двум агентам, ответы рядом для сравнения

### Рыночные данные
- **Акции / ETF / Индексы** — реальные котировки через Yahoo Finance (цена, P/E, дивиденды, капитализация)
- **Криптовалюты** — цены и топ-10 через CoinGecko (USD, EUR, RUB)
- **Форекс** — курсы валютных пар через Alpha Vantage
- **Технические индикаторы** — RSI, MACD, SMA, EMA, Bollinger Bands через Alpha Vantage
- **Графики котировок** — автоматическая генерация графиков на исторических данных

### Инструменты
- **Веб-поиск** — поиск через DuckDuckGo, результаты добавляются в контекст агента
- **Генерация графиков** — описание графика на естественном языке → matplotlib-визуализация
- **База знаний (RAG)** — загрузка документов, семантический поиск, агенты используют контекст из базы
- **Память агентов** — автоматическое извлечение и сохранение фактов между сессиями
- **Отчёты по расписанию** — настройка ежедневных/еженедельных отчётов от любого агента (APScheduler + cron)

### Администрирование
- **Whitelist с тегами** — доступ только для одобренных пользователей
- **Админ-панель** — управление юзерами, агентами и статистикой
- **История диалогов** — контекст сохраняется, можно сбросить и экспортировать

## Структура проекта

```
tg-multi-agent-bot/
├── bot.py                    # Точка входа
├── config.py                 # Конфигурация
├── seed_agents.py            # Начальная загрузка агентов
├── deploy.sh                 # Скрипт деплоя на VPS
├── requirements.txt          # Зависимости
├── db/                       # Слой базы данных (SQLite)
│   ├── connection.py         # Подключение и init
│   ├── agents.py             # Агенты
│   ├── history.py            # История диалогов
│   ├── memory.py             # Долгосрочная память
│   ├── scheduled.py          # Запланированные отчёты
│   ├── knowledge.py          # База знаний (RAG)
│   ├── state.py              # Состояние пользователя
│   └── ...
├── services/                 # Бизнес-логика
│   ├── llm.py                # OpenRouter API
│   ├── web_search.py         # DuckDuckGo поиск
│   ├── market_data.py        # Yahoo Finance + CoinGecko + Alpha Vantage
│   ├── charts.py             # Генерация графиков (matplotlib)
│   ├── rag.py                # Семантический поиск (TF-IDF)
│   ├── memory.py             # Извлечение фактов из диалога
│   ├── scheduler.py          # APScheduler для отчётов
│   └── text_utils.py         # Утилиты
├── handlers/                 # Обработчики
│   ├── multi_agent.py        # Мульти-агент + сравнение
│   ├── web_search.py         # Веб-поиск
│   ├── market.py             # Рыночные данные
│   ├── charts.py             # Графики
│   ├── knowledge.py          # База знаний
│   ├── memory.py             # Память
│   ├── scheduled.py          # Расписание
│   └── ...
├── keyboards/                # UI клавиатуры
└── middlewares/               # Middleware
```

## Установка

1. Клонируйте репозиторий
2. Скопируйте `.env.example` в `.env` и заполните ключи
3. Установите зависимости: `pip install -r requirements.txt`
4. Загрузите агентов: `python seed_agents.py`
5. Запустите: `python bot.py`

### Переменные окружения

| Переменная | Описание | Обязательно |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | Да |
| `OPENROUTER_API_KEY` | Ключ OpenRouter API | Да |
| `ADMIN_IDS` | Telegram ID админов (через запятую) | Да |
| `ALPHA_VANTAGE_KEY` | Ключ Alpha Vantage (Forex, индикаторы) | Нет |

## Деплой на VPS

```bash
chmod +x deploy.sh && ./deploy.sh
```

## Технологии

- Python 3.10+
- aiogram 3
- aiohttp
- SQLite
- OpenRouter API (Claude Opus 4.6)
- APScheduler
- yfinance, matplotlib, numpy
