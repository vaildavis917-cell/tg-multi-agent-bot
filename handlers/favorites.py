"""
Хендлеры избранных агентов.
"""

import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.favorites import add_favorite, remove_favorite, get_favorites
from db.agents import get_agent, get_agents
from keyboards.favorites_kb import favorites_list_kb

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "menu:favorites")
async def cb_favorites_list(callback: CallbackQuery, **kwargs):
    """Показать список избранных агентов."""
    uid = callback.from_user.id
    fav_ids = get_favorites(uid)

    if not fav_ids:
        await callback.answer("⭐ У вас пока нет избранных агентов. Выберите агента и добавьте в избранное.", show_alert=True)
        return

    agents = []
    for aid in fav_ids:
        a = get_agent(aid)
        if a and a["is_active"]:
            agents.append(a)

    if not agents:
        await callback.answer("⭐ Избранные агенты не найдены.", show_alert=True)
        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "⭐ **Избранные агенты:**",
        parse_mode="Markdown",
        reply_markup=favorites_list_kb(agents),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("fav:add:"))
async def cb_fav_add(callback: CallbackQuery, **kwargs):
    """Добавить агента в избранное."""
    agent_id = int(callback.data.split(":")[2])
    uid = callback.from_user.id

    added = add_favorite(uid, agent_id)
    if added:
        await callback.answer("⭐ Добавлено в избранное!", show_alert=False)
    else:
        await callback.answer("Уже в избранном", show_alert=False)


@router.callback_query(F.data.startswith("fav:remove:"))
async def cb_fav_remove(callback: CallbackQuery, **kwargs):
    """Убрать агента из избранного."""
    agent_id = int(callback.data.split(":")[2])
    uid = callback.from_user.id

    removed = remove_favorite(uid, agent_id)
    if removed:
        await callback.answer("☆ Убрано из избранного", show_alert=False)
    else:
        await callback.answer("Не было в избранном", show_alert=False)
