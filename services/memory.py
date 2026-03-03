"""
Сервис долгосрочной памяти — извлекает ключевые факты из диалога
и сохраняет их для будущих сессий.
"""

import logging
import json
from services.llm import chat_completion
from db.memory import save_memory, get_memories

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """Ты — система извлечения фактов. Проанализируй последние сообщения диалога
и извлеки КЛЮЧЕВЫЕ факты о пользователе, которые стоит запомнить для будущих сессий.

Категории фактов:
- portfolio: информация о портфеле, активах, инвестициях
- preferences: предпочтения, стиль инвестирования, риск-профиль
- goals: финансовые цели, планы
- personal: имя, профессия, опыт
- context: важный контекст для будущих разговоров

Верни JSON-массив фактов (или пустой массив если новых фактов нет):
[
  {"fact": "Инвестирует в ETF на S&P 500", "category": "portfolio"},
  {"fact": "Предпочитает долгосрочные инвестиции", "category": "preferences"}
]

ВАЖНО: Извлекай только НОВЫЕ, КОНКРЕТНЫЕ факты. Не повторяй общие фразы.
Если новых фактов нет — верни пустой массив [].
Верни ТОЛЬКО JSON, без пояснений."""


async def extract_and_save_memories(
    user_id: int,
    agent_id: int,
    messages: list[dict],
    max_messages: int = 6,
):
    """
    Извлекает факты из последних сообщений и сохраняет в память.
    Вызывается периодически (каждые N сообщений).
    """
    if len(messages) < 4:
        return

    # Берём последние N сообщений
    recent = messages[-max_messages:]
    dialog_text = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Agent'}: {m['content'][:500]}"
        for m in recent
    )

    # Получаем существующие факты чтобы не дублировать
    existing = get_memories(user_id, agent_id, limit=30)
    existing_facts = [m["fact"] for m in existing]

    prompt = (
        f"{EXTRACT_PROMPT}\n\n"
        f"Уже известные факты (НЕ дублировать):\n"
        + "\n".join(f"- {f}" for f in existing_facts[-10:])
        + f"\n\nДиалог:\n{dialog_text}"
    )

    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="Ты система извлечения фактов. Отвечай только JSON.",
        )

        content = result["content"].strip()
        # Убираем markdown-обёртку если есть
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        facts = json.loads(content)

        if not isinstance(facts, list):
            return

        saved = 0
        for f in facts:
            if isinstance(f, dict) and "fact" in f:
                fact_text = f["fact"].strip()
                category = f.get("category", "general")

                # Проверяем на дубликаты
                if fact_text and fact_text not in existing_facts:
                    save_memory(user_id, agent_id, fact_text, category)
                    saved += 1

        if saved:
            logger.info("Saved %d new facts for user %d, agent %d", saved, user_id, agent_id)

    except json.JSONDecodeError:
        logger.debug("Failed to parse memory extraction JSON")
    except Exception as e:
        logger.error("Memory extraction error: %s", e)
