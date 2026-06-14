from datetime import datetime, timedelta, timezone
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func

from database.db import (
    AsyncSessionLocal, get_user_by_telegram_id, get_user_by_cabinet_id,
    get_all_users, get_new_users_since, get_open_tickets, User, SupportTicket
)
from utils.keyboards import admin_menu, admin_back, ticket_answer_kb
from utils.states import AdminStates
from utils.helpers import fmt_date, sub_status
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── Фильтр доступа ────────────────────────────────────────

async def admin_check(event, **kwargs) -> bool:
    uid = getattr(event, "from_user", None)
    if uid:
        return is_admin(uid.id)
    return False


# ── Вход в панель ─────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "🛡 <b>Панель администратора HalvexVPN</b>",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin_back")
async def cb_admin_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text(
        "🛡 <b>Панель администратора HalvexVPN</b>",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )
    await callback.answer()


# ── Статистика ────────────────────────────────────────────

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        total = (await session.execute(select(func.count()).select_from(User))).scalar()
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(hours=24)
        new_day = (await session.execute(
            select(func.count()).where(User.created_at >= day_ago)
        )).scalar()
        active_sub = (await session.execute(
            select(func.count()).where(User.subscription_until > now)
        )).scalar()
        open_tickets = (await session.execute(
            select(func.count()).where(SupportTicket.is_answered == False)
        )).scalar()

    text = (
        f"📊 <b>Статистика HalvexVPN</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"🆕 Новых за 24ч: <b>{new_day}</b>\n"
        f"✅ Активных подписок: <b>{active_sub}</b>\n"
        f"🎫 Открытых тикетов: <b>{open_tickets}</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back())
    await callback.answer()


# ── Все пользователи ──────────────────────────────────────

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        users = await get_all_users(session)

    if not users:
        await callback.answer("Нет пользователей", show_alert=True)
        return

    lines = []
    for u in users[:30]:  # последние 30
        name = u.full_name or "—"
        uname = f"@{u.username}" if u.username else "нет"
        lines.append(
            f"🪪 <code>{u.cabinet_id}</code> | {name} {uname} | 💰{u.balance:.0f}₽"
        )

    text = f"👥 <b>Пользователи ({len(users)} всего, показаны последние 30):</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back())
    await callback.answer()


# ── Новые за 24ч ──────────────────────────────────────────

@router.callback_query(F.data == "admin_new_users")
async def admin_new_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    async with AsyncSessionLocal() as session:
        users = await get_new_users_since(session, since)

    if not users:
        await callback.answer("Новых пользователей нет", show_alert=True)
        return

    lines = []
    for u in users:
        name = u.full_name or "—"
        uname = f"@{u.username}" if u.username else "нет"
        lines.append(f"🆕 {name} {uname} | <code>{u.cabinet_id}</code> | {fmt_date(u.created_at)}")

    text = f"🆕 <b>Новые пользователи за 24ч ({len(users)}):</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_back())
    await callback.answer()


# ── Тикеты поддержки ──────────────────────────────────────

@router.callback_query(F.data == "admin_tickets")
async def admin_tickets(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        tickets = await get_open_tickets(session)

    if not tickets:
        await callback.answer("Открытых тикетов нет ✅", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    for t in tickets:
        builder.row(InlineKeyboardButton(
            text=f"🎫 #{t.id} — {fmt_date(t.created_at)}",
            callback_data=f"view_ticket_{t.id}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back"))

    await callback.message.edit_text(
        f"🎫 <b>Открытые тикеты ({len(tickets)}):</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    ticket_id = int(callback.data.split("_")[-1])

    async with AsyncSessionLocal() as session:
        ticket = await session.get(SupportTicket, ticket_id)
        if not ticket:
            await callback.answer("Тикет не найден", show_alert=True)
            return
        user = await session.get(User, ticket.user_id)

    text = (
        f"🎫 <b>Тикет #{ticket.id}</b>\n\n"
        f"👤 {user.full_name or '—'} (@{user.username or 'нет'})\n"
        f"🪪 <code>{user.cabinet_id}</code>\n"
        f"📅 {fmt_date(ticket.created_at)}\n\n"
        f"💬 <i>{ticket.message}</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=ticket_answer_kb(ticket_id))
    await callback.answer()


@router.callback_query(F.data.startswith("answer_ticket_"))
async def start_answer_ticket(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    ticket_id = int(callback.data.split("_")[-1])
    await state.set_state(AdminStates.answer_ticket_text)
    await state.update_data(ticket_id=ticket_id)
    await callback.message.edit_text(
        f"✏️ Введите ответ на тикет <b>#{ticket_id}</b>:",
        parse_mode="HTML",
        reply_markup=admin_back()
    )
    await callback.answer()


@router.message(AdminStates.answer_ticket_text)
async def send_ticket_answer(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    ticket_id = data.get("ticket_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        ticket = await session.get(SupportTicket, ticket_id)
        if not ticket:
            await message.answer("❌ Тикет не найден.")
            return
        user = await session.get(User, ticket.user_id)
        ticket.is_answered = True
        ticket.answer = message.text
        await session.commit()

    # Отправляем ответ пользователю
    bot: Bot = message.bot
    try:
        await bot.send_message(
            user.telegram_id,
            f"💬 <b>Ответ от поддержки HalvexVPN</b>\n\n"
            f"📩 Ваш вопрос:\n<i>{ticket.message}</i>\n\n"
            f"✅ Ответ:\n{message.text}",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await message.answer(
        f"✅ Ответ на тикет <b>#{ticket_id}</b> отправлен пользователю.",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )


# ── Рассылка ──────────────────────────────────────────────

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.broadcast_text)
    await callback.message.edit_text(
        "📢 <b>Рассылка</b>\n\nВведите текст сообщения для всех пользователей:",
        parse_mode="HTML",
        reply_markup=admin_back()
    )
    await callback.answer()


@router.message(AdminStates.broadcast_text)
async def do_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()

    async with AsyncSessionLocal() as session:
        users = await get_all_users(session)

    bot: Bot = message.bot
    sent = 0
    failed = 0
    for u in users:
        try:
            await bot.send_message(
                u.telegram_id,
                f"📢 <b>Сообщение от HalvexVPN:</b>\n\n{message.text}",
                parse_mode="HTML"
            )
            sent += 1
        except Exception:
            failed += 1

    await message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"📨 Отправлено: <b>{sent}</b>\n"
        f"❌ Ошибок: <b>{failed}</b>",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )


# ── Поиск пользователя ────────────────────────────────────

@router.callback_query(F.data == "admin_find_user")
async def admin_find_user(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.find_user_input)
    await callback.message.edit_text(
        "🔎 Введите ID кабинета (HVX-XXXXXX) или Telegram ID пользователя:",
        reply_markup=admin_back()
    )
    await callback.answer()


@router.message(AdminStates.find_user_input)
async def find_user_result(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    query = message.text.strip()

    async with AsyncSessionLocal() as session:
        user = None
        if query.startswith("HVX-"):
            user = await get_user_by_cabinet_id(session, query)
        elif query.isdigit():
            user = await get_user_by_telegram_id(session, int(query))

    if not user:
        await message.answer("❌ Пользователь не найден.", reply_markup=admin_menu())
        return

    text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🪪 Кабинет: <code>{user.cabinet_id}</code>\n"
        f"👤 Имя: {user.full_name or '—'}\n"
        f"📱 Username: @{user.username or 'нет'}\n"
        f"🆔 TG ID: <code>{user.telegram_id}</code>\n"
        f"💰 Баланс: <b>{user.balance:.0f} ₽</b>\n"
        f"📡 Подписка: {sub_status(user.subscription_until)}\n"
        f"🚫 Бан: {'Да' if user.is_banned else 'Нет'}\n"
        f"📅 Регистрация: {fmt_date(user.created_at)}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=admin_menu())


# ── Начислить баланс ──────────────────────────────────────

@router.callback_query(F.data == "admin_add_balance")
async def admin_add_balance_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.add_balance_id)
    await callback.message.edit_text(
        "💸 Введите ID кабинета (HVX-XXXXXX) или TG ID пользователя:",
        reply_markup=admin_back()
    )
    await callback.answer()


@router.message(AdminStates.add_balance_id)
async def admin_add_balance_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    query = message.text.strip()

    async with AsyncSessionLocal() as session:
        user = None
        if query.startswith("HVX-"):
            user = await get_user_by_cabinet_id(session, query)
        elif query.isdigit():
            user = await get_user_by_telegram_id(session, int(query))

    if not user:
        await message.answer("❌ Пользователь не найден.", reply_markup=admin_menu())
        await state.clear()
        return

    await state.update_data(target_user_id=user.id)
    await state.set_state(AdminStates.add_balance_amount)
    await message.answer(
        f"✅ Пользователь найден: <b>{user.full_name or '—'}</b> | <code>{user.cabinet_id}</code>\n"
        f"Введите сумму для начисления (в рублях):",
        parse_mode="HTML",
        reply_markup=admin_back()
    )


@router.message(AdminStates.add_balance_amount)
async def admin_add_balance_amount(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число.")
        return

    data = await state.get_data()
    await state.clear()
    target_id = data.get("target_user_id")

    async with AsyncSessionLocal() as session:
        user = await session.get(User, target_id)
        if not user:
            await message.answer("❌ Пользователь не найден.")
            return
        user.balance += amount
        await session.commit()

    bot: Bot = message.bot
    try:
        await bot.send_message(
            user.telegram_id,
            f"💰 <b>Баланс пополнен!</b>\n\n"
            f"Вам начислено <b>{amount:.0f} ₽</b>.\n"
            f"Текущий баланс: <b>{user.balance:.0f} ₽</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await message.answer(
        f"✅ Начислено <b>{amount:.0f} ₽</b> пользователю <code>{user.cabinet_id}</code>.",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )


# ── Бан / Разбан ──────────────────────────────────────────

@router.callback_query(F.data == "admin_ban")
async def admin_ban_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.ban_user_input)
    await callback.message.edit_text(
        "🚫 Введите ID кабинета или TG ID для бана/разбана:",
        reply_markup=admin_back()
    )
    await callback.answer()


@router.message(AdminStates.ban_user_input)
async def admin_ban_action(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    query = message.text.strip()

    async with AsyncSessionLocal() as session:
        user = None
        if query.startswith("HVX-"):
            user = await get_user_by_cabinet_id(session, query)
        elif query.isdigit():
            user = await get_user_by_telegram_id(session, int(query))

        if not user:
            await message.answer("❌ Пользователь не найден.", reply_markup=admin_menu())
            return

        user.is_banned = not user.is_banned
        action = "забанен 🚫" if user.is_banned else "разбанен ✅"
        await session.commit()

    await message.answer(
        f"Пользователь <code>{user.cabinet_id}</code> {action}.",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )
