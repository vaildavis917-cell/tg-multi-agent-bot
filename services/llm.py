"""
Взаимодействие с LLM через OpenRouter API.
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


async def chat_completion(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> dict:
    """
    Полный (не-streaming) запрос к LLM.
    Возвращает: {"content": str, "tokens_in": int, "tokens_out": int}
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
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers=_HEADERS,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    logger.error("OpenRouter %s: %s", resp.status, err)
                    return {"content": f"⚠️ Ошибка API ({resp.status}). Попробуйте позже.", "tokens_in": 0, "tokens_out": 0}

                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return {
                    "content": content,
                    "tokens_in": usage.get("prompt_tokens", 0),
                    "tokens_out": usage.get("completion_tokens", 0),
                }
    except Exception as e:
        logger.error("LLM request failed: %s", e)
        return {"content": "⚠️ Ошибка при обращении к AI. Попробуйте позже.", "tokens_in": 0, "tokens_out": 0}
