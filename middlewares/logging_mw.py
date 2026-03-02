"""
Middleware логирования входящих событий.
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            txt = (event.text or "(no text)")[:80]
            logger.info("[MSG] uid=%s @%s: %s", event.from_user.id, event.from_user.username, txt)
        elif isinstance(event, CallbackQuery) and event.from_user:
            logger.info("[CB]  uid=%s @%s: %s", event.from_user.id, event.from_user.username, event.data)
        return await handler(event, data)
