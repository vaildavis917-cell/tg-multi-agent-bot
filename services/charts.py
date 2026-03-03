"""
Генерация графиков и визуализаций через matplotlib.
Агент генерирует код Python → мы выполняем его → отправляем картинку.
"""

import logging
import os
import json
import tempfile
import subprocess
from typing import Optional
from services.llm import chat_completion

logger = logging.getLogger(__name__)

CHART_DIR = "/tmp/charts"
os.makedirs(CHART_DIR, exist_ok=True)

CHART_PROMPT = """Ты — генератор графиков. Пользователь просит визуализацию данных.
Напиши ПОЛНЫЙ Python-скрипт, который создаёт график с помощью matplotlib и сохраняет его.

ПРАВИЛА:
1. Используй matplotlib.pyplot и при необходимости numpy/pandas
2. Сохраняй график в файл: plt.savefig("{output_path}", dpi=150, bbox_inches='tight')
3. Используй plt.style.use('seaborn-v0_8-darkgrid') для красивого стиля
4. Добавляй заголовок, подписи осей, легенду
5. Используй русский язык для подписей
6. Если данные не указаны — создай реалистичные примерные данные
7. НЕ используй plt.show()
8. Верни ТОЛЬКО код Python, без пояснений, без markdown-обёртки

Запрос пользователя: {user_request}"""


async def generate_chart(user_request: str, chart_id: str = "chart") -> Optional[str]:
    """
    Генерирует график по запросу пользователя.
    Возвращает путь к файлу или None.
    """
    output_path = os.path.join(CHART_DIR, f"{chart_id}.png")

    prompt = CHART_PROMPT.format(
        output_path=output_path,
        user_request=user_request,
    )

    try:
        result = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="Ты генератор Python-кода для графиков. Отвечай ТОЛЬКО кодом.",
        )

        code = result["content"].strip()

        # Убираем markdown-обёртку
        if code.startswith("```python"):
            code = code[len("```python"):].strip()
        if code.startswith("```"):
            code = code[3:].strip()
        if code.endswith("```"):
            code = code[:-3].strip()

        # Сохраняем скрипт
        script_path = os.path.join(CHART_DIR, f"{chart_id}.py")
        with open(script_path, "w") as f:
            f.write(code)

        # Выполняем скрипт
        proc = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=CHART_DIR,
        )

        if proc.returncode != 0:
            logger.error("Chart script error: %s", proc.stderr)
            # Пробуем исправить ошибку
            return await _retry_chart(code, proc.stderr, output_path, chart_id)

        if os.path.exists(output_path):
            logger.info("Chart generated: %s", output_path)
            return output_path
        else:
            logger.error("Chart file not created")
            return None

    except subprocess.TimeoutExpired:
        logger.error("Chart generation timeout")
        return None
    except Exception as e:
        logger.error("Chart generation error: %s", e)
        return None


async def _retry_chart(
    original_code: str,
    error: str,
    output_path: str,
    chart_id: str,
) -> Optional[str]:
    """Пытается исправить ошибку в коде графика."""
    try:
        fix_prompt = (
            f"Этот Python-код для графика вызвал ошибку:\n\n"
            f"```python\n{original_code}\n```\n\n"
            f"Ошибка:\n{error}\n\n"
            f"Исправь код. Сохраняй в: {output_path}\n"
            f"Верни ТОЛЬКО исправленный код Python."
        )

        result = await chat_completion(
            messages=[{"role": "user", "content": fix_prompt}],
            system_prompt="Ты исправляешь Python-код. Отвечай ТОЛЬКО кодом.",
        )

        code = result["content"].strip()
        if code.startswith("```python"):
            code = code[len("```python"):].strip()
        if code.startswith("```"):
            code = code[3:].strip()
        if code.endswith("```"):
            code = code[:-3].strip()

        script_path = os.path.join(CHART_DIR, f"{chart_id}_fix.py")
        with open(script_path, "w") as f:
            f.write(code)

        proc = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=CHART_DIR,
        )

        if proc.returncode == 0 and os.path.exists(output_path):
            return output_path

    except Exception as e:
        logger.error("Chart retry error: %s", e)

    return None


async def generate_chart_from_data(
    data: dict,
    chart_type: str = "line",
    title: str = "График",
    chart_id: str = "data_chart",
) -> Optional[str]:
    """
    Генерирует график из структурированных данных.
    data: {"labels": [...], "values": [...]} или {"x": [...], "y": [...]}
    chart_type: line, bar, pie, scatter, area
    """
    output_path = os.path.join(CHART_DIR, f"{chart_id}.png")

    request = (
        f"Создай {chart_type}-график с заголовком '{title}'.\n"
        f"Данные: {json.dumps(data, ensure_ascii=False)}\n"
        f"Сохрани в {output_path}"
    )

    return await generate_chart(request, chart_id)
