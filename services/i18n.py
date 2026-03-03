"""
Мультиязычность — определение языка пользователя и локализация интерфейса.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Словарь переводов: ключ → {lang: текст}
TRANSLATIONS = {
    "main_menu": {
        "ru": "📋 **Главное меню:**",
        "en": "📋 **Main Menu:**",
    },
    "choose_agent": {
        "ru": "🤖 **Выберите агента:**",
        "en": "🤖 **Choose an agent:**",
    },
    "free_chat_title": {
        "ru": "💬 **Свободный чат с Claude Opus 4.6**\n\nПишите сообщения — бот ответит без системного промпта агента.",
        "en": "💬 **Free Chat with Claude Opus 4.6**\n\nSend messages — the bot will respond without an agent's system prompt.",
    },
    "no_access": {
        "ru": "🚫 У вас нет доступа к этому боту.\nВаш ID: `{uid}`\n\nОбратитесь к администратору.",
        "en": "🚫 You don't have access to this bot.\nYour ID: `{uid}`\n\nContact the administrator.",
    },
    "thinking": {
        "ru": "⏳ Думаю...",
        "en": "⏳ Thinking...",
    },
    "generating": {
        "ru": "⏳ _Генерирую..._",
        "en": "⏳ _Generating..._",
    },
    "dialog_reset": {
        "ru": "🔄 Диалог сброшен.",
        "en": "🔄 Dialog reset.",
    },
    "history_cleared": {
        "ru": "🔄 История очищена ({count} сообщений).\n\n📋 **Главное меню:**",
        "en": "🔄 History cleared ({count} messages).\n\n📋 **Main Menu:**",
    },
    "voice_recognizing": {
        "ru": "🎤 Распознаю голос...",
        "en": "🎤 Recognizing voice...",
    },
    "voice_recognized": {
        "ru": "🎤 Распознано: _{text}_\n\n⏳ Обрабатываю...",
        "en": "🎤 Recognized: _{text}_\n\n⏳ Processing...",
    },
    "voice_failed": {
        "ru": "❌ Не удалось распознать голосовое сообщение. Попробуйте ещё раз или напишите текстом.",
        "en": "❌ Failed to recognize voice message. Try again or type your message.",
    },
    "choose_mode": {
        "ru": "Выберите режим через меню 👇",
        "en": "Choose a mode from the menu 👇",
    },
    "export_empty": {
        "ru": "📭 История пуста — нечего экспортировать.",
        "en": "📭 History is empty — nothing to export.",
    },
    "no_favorites": {
        "ru": "⭐ У вас пока нет избранных агентов.",
        "en": "⭐ You have no favorite agents yet.",
    },
    "added_to_favorites": {
        "ru": "⭐ Добавлено в избранное!",
        "en": "⭐ Added to favorites!",
    },
    "removed_from_favorites": {
        "ru": "☆ Убрано из избранного",
        "en": "☆ Removed from favorites",
    },
    "file_processing": {
        "ru": "📎 Обрабатываю файл `{filename}`...",
        "en": "📎 Processing file `{filename}`...",
    },
    "file_unsupported": {
        "ru": "❌ Формат `{ext}` не поддерживается.",
        "en": "❌ Format `{ext}` is not supported.",
    },
    "file_too_big": {
        "ru": "❌ Файл слишком большой (макс 20 MB).",
        "en": "❌ File is too large (max 20 MB).",
    },
    # Кнопки
    "btn_agents": {
        "ru": "🤖 Выбрать агента",
        "en": "🤖 Choose Agent",
    },
    "btn_free_chat": {
        "ru": "💬 Свободный чат с LLM",
        "en": "💬 Free Chat with LLM",
    },
    "btn_favorites": {
        "ru": "⭐ Избранные агенты",
        "en": "⭐ Favorite Agents",
    },
    "btn_clear_history": {
        "ru": "🔄 Сбросить историю",
        "en": "🔄 Clear History",
    },
    "btn_help": {
        "ru": "ℹ️ Помощь",
        "en": "ℹ️ Help",
    },
    "btn_admin": {
        "ru": "⚙️ Админ-панель",
        "en": "⚙️ Admin Panel",
    },
    "btn_settings": {
        "ru": "🌐 Язык / Language",
        "en": "🌐 Language / Язык",
    },
    "btn_back": {
        "ru": "◀️ Назад в меню",
        "en": "◀️ Back to Menu",
    },
    "btn_reset_dialog": {
        "ru": "🔄 Сбросить диалог",
        "en": "🔄 Reset Dialog",
    },
    "btn_about_agent": {
        "ru": "📋 Об агенте",
        "en": "📋 About Agent",
    },
    "btn_templates": {
        "ru": "⚡ Быстрые запросы",
        "en": "⚡ Quick Prompts",
    },
    "btn_export": {
        "ru": "📄 Экспорт диалога",
        "en": "📄 Export Dialog",
    },
    "btn_clear_free": {
        "ru": "🔄 Сбросить диалог",
        "en": "🔄 Reset Dialog",
    },
    "btn_export_free": {
        "ru": "📄 Экспорт",
        "en": "📄 Export",
    },
    "lang_select": {
        "ru": "🌐 **Выберите язык:**",
        "en": "🌐 **Select language:**",
    },
    "lang_set": {
        "ru": "✅ Язык установлен: Русский",
        "en": "✅ Language set: English",
    },
}

# Язык по умолчанию
DEFAULT_LANG = "ru"


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """Получить перевод по ключу."""
    lang = lang or DEFAULT_LANG
    translations = TRANSLATIONS.get(key, {})
    text = translations.get(lang, translations.get(DEFAULT_LANG, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def detect_language(text: str) -> str:
    """Простое определение языка по символам."""
    ru_chars = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
    en_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    return "ru" if ru_chars >= en_chars else "en"
