"""
Хендлеры выбора агента и взаимодействия с ним.
"""

import os
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from db.agents import get_agents, get_agent
from db.state import set_user_state
from db.history import clear_history
from db.favorites import is_favorite
from keyboards import agents_list_kb, agent_selected_kb

router = Router()
logger = logging.getLogger(__name__)

# Маппинг agent_id -> файл картинки
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

AGENT_IMAGES = {
    1: "agent_1_goldman.png",
    2: "agent_2_morgan.png",
    3: "agent_3_bridgewater.png",
    4: "agent_4_jpmorgan.png",
    5: "agent_5_blackrock.png",
    6: "agent_6_citadel.png",
    7: "agent_7_harvard.png",
    8: "agent_8_bain.png",
}


def _get_agent_photo(agent_id: int):
    """Возвращает FSInputFile для фото агента или None."""
    filename = AGENT_IMAGES.get(agent_id)
    if not filename:
        return None
    path = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(path):
        return FSInputFile(path)
    logger.warning("Image not found: %s", path)
    return None


def _agent_kb(agent_id: int, user_id: int):
    """Клавиатура агента с учётом избранного."""
    fav = is_favorite(user_id, agent_id)
    return agent_selected_kb(agent_id, is_fav=fav)


@router.message(Command("agents"))
async def cmd_agents(message: Message, **kwargs):
    agents = get_agents(active_only=True)
    if not agents:
        await message.answer("😔 Пока нет доступных агентов.")
        return
    await message.answer("🤖 **Выберите агента:**", parse_mode="Markdown", reply_markup=agents_list_kb(agents))


@router.callback_query(F.data == "menu:agents")
async def cb_agents_list(callback: CallbackQuery, **kwargs):
    agents = get_agents(active_only=True)
    if not agents:
        await callback.message.edit_text("😔 Пока нет доступных агентов.")
        await callback.answer()
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "🤖 **Выберите агента:**",
        parse_mode="Markdown",
        reply_markup=agents_list_kb(agents),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("agent:select:"))
async def cb_agent_select(callback: CallbackQuery, **kwargs):
    agent_id = int(callback.data.split(":")[2])
    agent = get_agent(agent_id)
    if not agent:
        await callback.answer("❌ Агент не найден", show_alert=True)
        return

    uid = callback.from_user.id
    set_user_state(uid, "agent", agent_id)

    caption = (
        f"{agent['emoji']} **Агент: {agent['name']}**\n\n"
        f"_{agent['description']}_\n\n"
        "Отправьте сообщение для начала диалога."
    )

    photo = _get_agent_photo(agent_id)
    kb = _agent_kb(agent_id, uid)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if photo:
        await callback.message.answer_photo(
            photo=photo, caption=caption, parse_mode="Markdown", reply_markup=kb,
        )
    else:
        await callback.message.answer(caption, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("agent:clear:"))
async def cb_agent_clear(callback: CallbackQuery, **kwargs):
    agent_id = int(callback.data.split(":")[2])
    uid = callback.from_user.id
    clear_history(uid, agent_id)
    agent = get_agent(agent_id)
    name = agent["name"] if agent else "Агент"

    caption = f"🔄 Диалог с **{name}** сброшен. Можете начать заново."
    photo = _get_agent_photo(agent_id) if agent else None
    kb = _agent_kb(agent_id, uid)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if photo:
        await callback.message.answer_photo(
            photo=photo, caption=caption, parse_mode="Markdown", reply_markup=kb,
        )
    else:
        await callback.message.answer(caption, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("agent:info:"))
async def cb_agent_info(callback: CallbackQuery, **kwargs):
    agent_id = int(callback.data.split(":")[2])
    agent = get_agent(agent_id)
    if not agent:
        await callback.answer("❌ Агент не найден", show_alert=True)
        return

    uid = callback.from_user.id
    status = "✅ Активен" if agent["is_active"] else "❌ Неактивен"
    caption = (
        f"{agent['emoji']} **{agent['name']}**\n\n"
        f"📝 {agent['description']}\n"
        f"🆔 ID: `{agent['id']}`\n"
        f"📊 Статус: {status}"
    )

    photo = _get_agent_photo(agent_id)
    kb = _agent_kb(agent_id, uid)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if photo:
        await callback.message.answer_photo(
            photo=photo, caption=caption, parse_mode="Markdown", reply_markup=kb,
        )
    else:
        await callback.message.answer(caption, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()
