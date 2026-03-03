"""
Скрипт загрузки шаблонов быстрых запросов для агентов.
Запускается один раз после seed_agents.py.
"""

from db.connection import init_db
from db.templates import add_template, get_templates

TEMPLATES = {
    # agent_id: [(label, text), ...]
    1: [  # Goldman Sachs
        ("🏗 Tech-сектор", "Мой профиль: умеренный риск, $50K, горизонт 3 года, предпочитаю технологический сектор"),
        ("💊 Healthcare", "Мой профиль: консервативный, $100K, горизонт 5 лет, предпочитаю healthcare сектор"),
        ("⚡ Энергетика", "Мой профиль: агрессивный, $30K, горизонт 1 год, предпочитаю энергетический сектор"),
    ],
    2: [  # Morgan Stanley DCF
        ("🍎 Apple (AAPL)", "Проведи DCF-анализ для Apple (AAPL)"),
        ("🚗 Tesla (TSLA)", "Проведи DCF-анализ для Tesla (TSLA)"),
        ("☁️ Microsoft (MSFT)", "Проведи DCF-анализ для Microsoft (MSFT)"),
    ],
    3: [  # Bridgewater
        ("📊 Пример портфеля", "Мой портфель: AAPL 20%, MSFT 15%, GOOGL 15%, AMZN 10%, SPY 20%, BND 10%, GLD 10%. Общая стоимость $200K"),
        ("🏠 Консервативный", "Мой портфель: VTI 30%, BND 40%, GLD 15%, VNQ 15%. Общая стоимость $500K"),
    ],
    4: [  # JPMorgan
        ("🍎 Apple отчёт", "Компания Apple (AAPL), ближайший квартальный отчёт"),
        ("📦 Amazon отчёт", "Компания Amazon (AMZN), ближайший квартальный отчёт"),
        ("🤖 NVIDIA отчёт", "Компания NVIDIA (NVDA), ближайший квартальный отчёт"),
    ],
    5: [  # BlackRock
        ("👨‍💼 30 лет, средний", "Возраст 30, доход $80K/год, сбережения $50K, цель — рост капитала, умеренный риск, счёт Taxable"),
        ("👴 50 лет, консерв.", "Возраст 50, доход $120K/год, сбережения $300K, цель — пенсия через 15 лет, низкий риск, счёт 401K + IRA"),
    ],
    6: [  # Citadel
        ("🍎 Apple (AAPL)", "Тикер: AAPL, позиции нет"),
        ("🚗 Tesla (TSLA)", "Тикер: TSLA, long позиция от $180"),
        ("₿ Bitcoin (BTC)", "Тикер: BTC/USD, позиции нет"),
    ],
    7: [  # Гарвард
        ("💰 $100K портфель", "Сумма: $100K, желаемый доход: $500/мес, счёт Taxable, обычная налоговая ставка"),
        ("🏦 $500K пенсия", "Сумма: $500K, желаемый доход: $2000/мес, счёт IRA, пенсионер"),
    ],
    8: [  # Bain
        ("💻 Полупроводники", "Сектор: полупроводники (Semiconductors)"),
        ("☁️ Облачные сервисы", "Сектор: облачные вычисления (Cloud Computing)"),
        ("🏥 Биотех", "Сектор: биотехнологии (Biotech)"),
    ],
}


def seed():
    init_db()
    total = 0
    for agent_id, templates in TEMPLATES.items():
        existing = get_templates(agent_id)
        if existing:
            print(f"  ⏩ Агент {agent_id}: уже есть {len(existing)} шаблонов, пропускаю")
            continue
        for label, text in templates:
            add_template(agent_id, label, text)
            total += 1
        print(f"  ✅ Агент {agent_id}: загружено {len(templates)} шаблонов")
    print(f"\nВсего загружено {total} шаблонов.")


if __name__ == "__main__":
    seed()
