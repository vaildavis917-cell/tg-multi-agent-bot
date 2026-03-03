"""
Streaming-запросы к LLM через OpenRouter API.
Ответ приходит по частям — бот редактирует сообщение в реальном времени.
"""

import json
import logging
from typing import Optional, AsyncGenerator

import aiohttp

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL

logger = logging.getLogger(__name__)

_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://t.me/multi_agent_bot",
    "X-Title": "Multi-Agent TG Bot",
}


async def chat_completion_stream(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> AsyncGenerator[dict, None]:
    """
    Streaming запрос к LLM.
    Yields: {"type": "chunk", "content": str}
            {"type": "done", "content": str, "tokens_in": int, "tokens_out": int}
            {"type": "error", "content": str}
    """
    model = model or OPENROUTER_MODEL
    msgs = list(messages)
    if system_prompt:
        msgs = [{"role": "system", "content": system_prompt}] + msgs

    payload = {
        "model": model,
        "messages": msgs,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }

    full_content = ""
    tokens_in = 0
    tokens_out = 0

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers=_HEADERS,
                timeout=aiohttp.ClientTimeout(total=180),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    logger.error("OpenRouter stream %s: %s", resp.status, err)
                    yield {"type": "error", "content": f"⚠️ Ошибка API ({resp.status}). Попробуйте позже."}
                    return

                async for line in resp.content:
                    decoded = line.decode("utf-8").strip()
                    if not decoded or not decoded.startswith("data: "):
                        continue

                    data_str = decoded[6:]  # убираем "data: "

                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # Извлекаем chunk
                    choices = data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    chunk_text = delta.get("content", "")

                    if chunk_text:
                        full_content += chunk_text
                        yield {"type": "chunk", "content": full_content}

                    # Извлекаем usage если есть (обычно в последнем chunk)
                    usage = data.get("usage")
                    if usage:
                        tokens_in = usage.get("prompt_tokens", 0)
                        tokens_out = usage.get("completion_tokens", 0)

        yield {
            "type": "done",
            "content": full_content,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        }

    except Exception as e:
        logger.error("LLM stream failed: %s", e)
        if full_content:
            yield {
                "type": "done",
                "content": full_content,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
            }
        else:
            yield {"type": "error", "content": "⚠️ Ошибка при обращении к AI. Попробуйте позже."}
