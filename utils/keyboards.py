from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ── Главное меню ──────────────────────────────────────────

def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="balance_topup"),
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="subscription_extend"),
    )
    builder.row(
        InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral_menu"),
    )
    builder.row(
        InlineKeyboardButton(text="🛠 Тех. поддержка", callback_data="support_start"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile"),
    )
    return builder.as_markup()


# ── Тарифы ────────────────────────────────────────────────

def plans_keyboard() -> InlineKeyboardMarkup:
    from config import PLANS
    builder = InlineKeyboardBuilder()
    for key, plan in PLANS.items():
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {plan['label']} — {plan['price']} ₽",
                callback_data=f"plan_{key}",
            )
        )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"))
    return builder.as_markup()


# ── Назад ─────────────────────────────────────────────────

def back_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_main"))
    return builder.as_markup()


# ── Пополнение баланса ────────────────────────────────────

def topup_amounts() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    amounts = [100, 200, 500, 1000]
    for a in amounts:
        builder.button(text=f"{a} ₽", callback_data=f"topup_{a}")
    builder.row(InlineKeyboardButton(text="✏️ Другая сумма", callback_data="topup_custom"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"))
    builder.adjust(2)
    return builder.as_markup()


# ── Подтверждение оплаты ──────────────────────────────────

def confirm_payment(amount: int, action: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Оплатить", callback_data=f"confirm_pay_{action}_{amount}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="back_main"),
    )
    return builder.as_markup()


# ── Реферальное меню ──────────────────────────────────────

def referral_keyboard(ref_link: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔗 Скопировать ссылку", callback_data="copy_ref"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"))
    return builder.as_markup()


# ── Админ панель ──────────────────────────────────────────

def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Рассылка",         callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users"))
    builder.row(InlineKeyboardButton(text="🆕 Новые за 24ч",     callback_data="admin_new_users"))
    builder.row(InlineKeyboardButton(text="🎫 Тикеты поддержки", callback_data="admin_tickets"))
    builder.row(InlineKeyboardButton(text="📊 Статистика",       callback_data="admin_stats"))
    builder.row(InlineKeyboardButton(text="🔎 Найти юзера",      callback_data="admin_find_user"))
    builder.row(InlineKeyboardButton(text="💸 Начислить баланс", callback_data="admin_add_balance"))
    builder.row(InlineKeyboardButton(text="🚫 Бан / Разбан",     callback_data="admin_ban"))
    return builder.as_markup()


def admin_back() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Админ меню", callback_data="admin_back"))
    return builder.as_markup()


def ticket_answer_kb(ticket_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Ответить", callback_data=f"answer_ticket_{ticket_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_tickets"))
    return builder.as_markup()
