"""
Хендлер для управления базой знаний (RAG).
Загрузка документов, просмотр, удаление, поиск.
"""

import logging
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton,
    ContentType,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.knowledge import get_user_documents, delete_document, clear_knowledge_base
from services.rag import index_document, search_knowledge_base, format_rag_context
from services.file_parser import parse_file
from keyboards.common_kb import cancel_kb

logger = logging.getLogger(__name__)
router = Router()


class KBStates(StatesGroup):
    waiting_file = State()
    waiting_search = State()


# ═══════════════════════════════════════════════════════════
#  Меню базы знаний
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu:knowledge")
async def on_kb_menu(callback: CallbackQuery):
    """Показывает базу знаний."""
    uid = callback.from_user.id
    docs = get_user_documents(uid)

    if not docs:
        text = (
            "📚 **База знаний (RAG)**\n\n"
            "Ваша база знаний пуста.\n\n"
            "Загрузите документы (PDF, TXT, CSV, Excel) — "
            "агенты будут использовать их для ответов.\n\n"
            "Это как личная библиотека для ваших агентов!"
        )
    else:
        text = f"📚 **База знаний** — {len(docs)} документов\n\n"
        for d in docs:
            size_kb = d["size"] // 1024
            text += f"📄 #{d['id']} **{d['filename']}** ({size_kb} KB)\n"
            text += f"   Тип: {d['file_type']} | {d['created_at'][:10]}\n\n"

    buttons = [
        [InlineKeyboardButton(text="📤 Загрузить документ", callback_data="kb:upload")],
        [InlineKeyboardButton(text="🔍 Поиск по базе", callback_data="kb:search")],
    ]

    if docs:
        buttons.append([InlineKeyboardButton(text="🗑 Очистить базу", callback_data="kb:clear")])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  Загрузка документов
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "kb:upload")
async def on_kb_upload(callback: CallbackQuery, state: FSMContext):
    """Начало загрузки документа."""
    await state.set_state(KBStates.waiting_file)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "📤 **Загрузка в базу знаний**\n\n"
        "Отправьте файл одного из форматов:\n"
        "• 📄 PDF\n"
        "• 📝 TXT\n"
        "• 📊 Excel (XLSX)\n"
        "• 📋 CSV\n\n"
        "Или отправьте текст сообщением — он тоже будет добавлен.",
        reply_markup=cancel_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(KBStates.waiting_file, F.document)
async def on_kb_file(message: Message, state: FSMContext):
    """Получен файл для базы знаний."""
    await state.clear()
    uid = message.from_user.id

    status_msg = await message.answer("📥 Обрабатываю файл...")

    try:
        # Скачиваем файл
        file = await message.bot.get_file(message.document.file_id)
        file_path = f"/tmp/kb_{uid}_{message.document.file_name}"
        await message.bot.download_file(file.file_path, file_path)

        # Парсим содержимое
        content = parse_file(file_path)

        if not content or len(content.strip()) < 10:
            await status_msg.edit_text("⚠️ Файл пустой или не удалось извлечь текст.")
            return

        # Индексируем
        filename = message.document.file_name or "document"
        file_type = filename.rsplit(".", 1)[-1] if "." in filename else "text"
        n_chunks = await index_document(uid, filename, content, file_type)

        await status_msg.edit_text(
            f"✅ Документ добавлен в базу знаний!\n\n"
            f"📄 **{filename}**\n"
            f"📏 {len(content)} символов → {n_chunks} фрагментов\n\n"
            f"Теперь агенты могут использовать этот документ для ответов.",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error("KB file upload error: %s", e)
        await status_msg.edit_text(f"❌ Ошибка обработки файла: {e}")


@router.message(KBStates.waiting_file, F.text)
async def on_kb_text(message: Message, state: FSMContext):
    """Получен текст для базы знаний."""
    await state.clear()
    uid = message.from_user.id

    content = message.text.strip()
    if len(content) < 10:
        await message.answer("⚠️ Слишком короткий текст.")
        return

    # Берём первые 50 символов как название
    filename = content[:50].replace("\n", " ") + "..."
    n_chunks = await index_document(uid, filename, content, "text")

    await message.answer(
        f"✅ Текст добавлен в базу знаний!\n\n"
        f"📏 {len(content)} символов → {n_chunks} фрагментов",
    )


# ═══════════════════════════════════════════════════════════
#  Поиск по базе
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "kb:search")
async def on_kb_search(callback: CallbackQuery, state: FSMContext):
    """Начало поиска по базе."""
    await state.set_state(KBStates.waiting_search)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "🔍 Введите поисковый запрос по базе знаний:",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(KBStates.waiting_search)
async def on_kb_search_query(message: Message, state: FSMContext):
    """Поиск по базе знаний."""
    await state.clear()
    uid = message.from_user.id
    query = message.text.strip()

    results = search_knowledge_base(uid, query, top_k=5)

    if not results or all(r["score"] < 0.01 for r in results):
        await message.answer("🔍 Ничего не найдено по вашему запросу.")
        return

    text = f"🔍 Результаты поиска: «{query}»\n\n"
    for i, r in enumerate(results, 1):
        if r["score"] > 0.01:
            text += f"**{i}. Релевантность: {r['score']:.0%}**\n"
            text += f"{r['chunk_text'][:300]}...\n\n"

    from services.text_utils import split_text
    for part in split_text(text):
        try:
            await message.answer(part, parse_mode="Markdown")
        except Exception:
            await message.answer(part)


# ═══════════════════════════════════════════════════════════
#  Очистка базы
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data == "kb:clear")
async def on_kb_clear(callback: CallbackQuery):
    """Очищает базу знаний."""
    uid = callback.from_user.id
    clear_knowledge_base(uid)
    await callback.answer("🗑 База знаний очищена", show_alert=True)
    await on_kb_menu(callback)
