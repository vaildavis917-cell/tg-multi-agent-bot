"""
Middleware проверки доступа: whitelist + admin.
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from config import ADMIN_IDS
from db.whitelist import is_whitelisted

logger = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user

        if user is None:
            return

        uid = user.id

        # Админы — всегда пропускаем
        if uid in ADMIN_IDS:
            data["is_admin"] = True
            return await handler(event, data)

        # Whitelist
        if is_whitelisted(uid):
            data["is_admin"] = False
            return await handler(event, data)

        # Заблокировано
        logger.warning("Access denied: user_id=%s", uid)
        if isinstance(event, Message):
            await event.answer(
                "🚫 У вас нет доступа к этому боту.\n"
                f"Ваш ID: `{uid}`\n\n"
                "Обратитесь к администратору.",
                parse_mode="Markdown",
            )
        elif isinstance(event, CallbackQuery):
            await event.answer("🚫 Нет доступа", show_alert=True)
