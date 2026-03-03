"""
Хендлер экспорта диалогов в файл.
"""

import os
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

from db.state import get_user_state
from services.export import export_dialog_to_file

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("export:agent:"))
async def cb_export_agent(callback: CallbackQuery, **kwargs):
    """Экспорт диалога с конкретным агентом."""
    agent_id = int(callback.data.split(":")[2])
    uid = callback.from_user.id

    filepath = export_dialog_to_file(uid, agent_id=agent_id)
    if not filepath:
        await callback.answer("📭 История пуста — нечего экспортировать.", show_alert=True)
        return

    try:
        doc = FSInputFile(filepath, filename=os.path.basename(filepath))
        await callback.message.answer_document(doc, caption="📄 Экспорт диалога с агентом")
    except Exception as e:
        logger.error("Export failed: %s", e)
        await callback.answer("❌ Ошибка при экспорте", show_alert=True)
    finally:
        # Чистим временный файл
        try:
            os.remove(filepath)
            os.rmdir(os.path.dirname(filepath))
        except Exception:
            pass

    await callback.answer()


@router.callback_query(F.data == "export:free_chat")
async def cb_export_free(callback: CallbackQuery, **kwargs):
    """Экспорт свободного чата."""
    uid = callback.from_user.id

    filepath = export_dialog_to_file(uid, agent_id=None)
    if not filepath:
        await callback.answer("📭 История пуста — нечего экспортировать.", show_alert=True)
        return

    try:
        doc = FSInputFile(filepath, filename=os.path.basename(filepath))
        await callback.message.answer_document(doc, caption="📄 Экспорт свободного чата")
    except Exception as e:
        logger.error("Export failed: %s", e)
        await callback.answer("❌ Ошибка при экспорте", show_alert=True)
    finally:
        try:
            os.remove(filepath)
            os.rmdir(os.path.dirname(filepath))
        except Exception:
            pass

    await callback.answer()
