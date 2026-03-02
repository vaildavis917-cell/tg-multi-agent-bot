"""
Клавиатуры админ-панели: whitelist, агенты, статистика.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ── Главная панель ───────────────────────────────────────

def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Whitelist", callback_data="admin:whitelist")],
        [InlineKeyboardButton(text="🤖 Управление агентами", callback_data="admin:agents")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:back")],
    ])


# ── Whitelist ────────────────────────────────────────────

def admin_whitelist_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список пользователей", callback_data="admin:wl:list")],
        [InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="admin:wl:add")],
        [InlineKeyboardButton(text="➖ Удалить пользователя", callback_data="admin:wl:remove")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:panel")],
    ])


def admin_whitelist_list_kb(users: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for u in users:
        # Приоритет отображения: тег → username → full_name → ID
        tag = u.get("tag", "")
        username = u.get("username", "")
        full_name = u.get("full_name", "")
        label = tag or username or full_name or str(u["user_id"])
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {label} • {u['user_id']}",
                callback_data=f"admin:wl:info:{u['user_id']}",
            ),
            InlineKeyboardButton(text="❌", callback_data=f"admin:wl:del:{u['user_id']}"),
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin:whitelist")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Агенты ───────────────────────────────────────────────

def admin_agents_kb(agents: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for a in agents:
        status = "✅" if a["is_active"] else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {a['emoji']} {a['name']}",
                callback_data=f"admin:ag:edit:{a['id']}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="➕ Добавить агента", callback_data="admin:ag:add")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin:panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_agent_edit_kb(agent_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Имя", callback_data=f"admin:ag:set_name:{agent_id}")],
        [InlineKeyboardButton(text="😀 Эмодзи", callback_data=f"admin:ag:set_emoji:{agent_id}")],
        [InlineKeyboardButton(text="📝 Описание", callback_data=f"admin:ag:set_desc:{agent_id}")],
        [InlineKeyboardButton(text="🧠 Системный промпт", callback_data=f"admin:ag:set_prompt:{agent_id}")],
        [InlineKeyboardButton(text=toggle, callback_data=f"admin:ag:toggle:{agent_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin:ag:delete:{agent_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:agents")],
    ])
