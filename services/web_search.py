"""
Веб-поиск через DuckDuckGo (бесплатно, без API ключа).
Используется агентами для получения актуальных данных.
"""

import logging
import aiohttp
import json
from typing import Optional

logger = logging.getLogger(__name__)

DDGS_URL = "https://api.duckduckgo.com/"
DDGS_HTML_URL = "https://html.duckduckgo.com/html/"


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Поиск через DuckDuckGo HTML.
    Возвращает список: [{"title": ..., "url": ..., "snippet": ...}, ...]
    """
    results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        data = {"q": query, "b": ""}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                DDGS_HTML_URL,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    logger.warning("DuckDuckGo search failed: %s", resp.status)
                    return results

                html = await resp.text()

                # Парсим результаты из HTML
                results = _parse_ddg_html(html, max_results)

    except Exception as e:
        logger.error("Web search error: %s", e)

    return results


def _parse_ddg_html(html: str, max_results: int) -> list[dict]:
    """Парсит HTML-ответ DuckDuckGo."""
    results = []
    try:
        from html.parser import HTMLParser

        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self.current = {}
                self.in_result = False
                self.in_title = False
                self.in_snippet = False
                self.depth = 0

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                cls = attrs_dict.get("class", "")

                if tag == "div" and "result__body" in cls:
                    self.in_result = True
                    self.current = {"title": "", "url": "", "snippet": ""}

                if self.in_result:
                    if tag == "a" and "result__a" in cls:
                        self.in_title = True
                        href = attrs_dict.get("href", "")
                        self.current["url"] = href

                    if tag == "a" and "result__snippet" in cls:
                        self.in_snippet = True

            def handle_endtag(self, tag):
                if tag == "a" and self.in_title:
                    self.in_title = False
                if tag == "a" and self.in_snippet:
                    self.in_snippet = False
                    if self.current.get("title"):
                        self.results.append(self.current)
                    self.current = {}
                    self.in_result = False

            def handle_data(self, data):
                if self.in_title:
                    self.current["title"] += data.strip()
                if self.in_snippet:
                    self.current["snippet"] += data.strip()

        parser = DDGParser()
        parser.feed(html)
        results = parser.results[:max_results]

    except Exception as e:
        logger.error("DDG parse error: %s", e)

    return results


def format_search_results(results: list[dict]) -> str:
    """Форматирует результаты поиска в текст для контекста LLM."""
    if not results:
        return "Результаты поиска не найдены."

    parts = ["📌 Результаты веб-поиска:\n"]
    for i, r in enumerate(results, 1):
        parts.append(f"{i}. **{r['title']}**")
        if r.get("snippet"):
            parts.append(f"   {r['snippet']}")
        if r.get("url"):
            parts.append(f"   🔗 {r['url']}")
        parts.append("")

    return "\n".join(parts)
