# Multi-Agent Telegram Bot (Claude Opus 4.6)

Мульти-агентный Telegram бот на базе Claude Opus 4.6 через OpenRouter API. Бот предоставляет доступ к 8 специализированным финансовым AI-агентам и режиму свободного чата.

## Возможности

- **8 финансовых агентов** — каждый со своим системным промптом и ролью (Goldman Sachs, Morgan Stanley, Bridgewater, JPMorgan, BlackRock, Citadel, Harvard Endowment, Bain & Company)
- **Свободный чат** — прямое общение с Claude Opus 4.6 без ограничений
- **Whitelist с тегами** — доступ только для одобренных пользователей, каждому можно присвоить тег/имя
- **Админ-панель** — управление юзерами, агентами и статистикой прямо из бота
- **История диалогов** — контекст сохраняется, можно сбросить
- **Модульная архитектура** — каждый хендлер, клавиатура и модуль БД в отдельном файле

## Структура проекта

```
tg-multi-agent-bot/
├── bot.py                    # Точка входа
├── config.py                 # Конфигурация
├── seed_agents.py            # Начальная загрузка агентов
├── deploy.sh                 # Скрипт деплоя на VPS
├── requirements.txt          # Зависимости
├── .env.example              # Шаблон переменных окружения
├── db/                       # Слой базы данных (SQLite)
│   ├── connection.py
│   ├── whitelist.py
│   ├── agents.py
│   ├── history.py
│   ├── state.py
│   └── stats.py
├── services/                 # Бизнес-логика
│   ├── llm.py
│   └── text_utils.py
├── middlewares/               # Middleware
│   ├── access.py
│   └── logging_mw.py
├── keyboards/                # UI клавиатуры
│   ├── main_menu.py
│   ├── agents_kb.py
│   ├── free_chat_kb.py
│   ├── admin_kb.py
│   └── common_kb.py
└── handlers/                 # Обработчики
    ├── start.py
    ├── menu_nav.py
    ├── agents.py
    ├── free_chat.py
    ├── chat_router.py
    ├── admin_panel.py
    ├── admin_whitelist.py
    ├── admin_agents.py
    └── admin_stats.py
```

## Установка

1. Клонируйте репозиторий
2. Скопируйте `.env.example` в `.env` и заполните ключи
3. Установите зависимости: `pip install -r requirements.txt`
4. Загрузите агентов: `python seed_agents.py`
5. Запустите: `python bot.py`

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
