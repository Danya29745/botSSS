from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.db import AsyncSessionLocal, get_user_by_telegram_id, create_support_ticket
from utils.keyboards import back_main
from utils.states import SupportStates
from config import ADMIN_IDS

router = Router()


@router.callback_query(F.data == "support_start")
async def support_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_message)
    await callback.message.edit_text(
        "🛠 <b>Техническая поддержка</b>\n\n"
        "Опишите вашу проблему или задайте вопрос.\n"
        "Мы ответим в ближайшее время ⚡️\n\n"
        "✏️ Напишите ваше сообщение:",
        parse_mode="HTML",
        reply_markup=back_main()
    )
    await callback.answer()


@router.message(SupportStates.waiting_for_message)
async def receive_support_message(message: Message, state: FSMContext):
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("❌ Профиль не найден.", reply_markup=back_main())
            return
        ticket = await create_support_ticket(session, user.id, message.text)
        cabinet_id = user.cabinet_id
        username = user.username or "нет"
        full_name = user.full_name or "—"
        ticket_id = ticket.id

    # Подтверждение юзеру
    await message.answer(
        "✅ <b>Сообщение отправлено!</b>\n\n"
        "📬 Ваш вопрос принят — мы ответим в ближайшее время.\n"
        "Ответ придёт сюда, в бот.",
        parse_mode="HTML",
        reply_markup=back_main()
    )

    # Уведомление всем админам
    bot: Bot = message.bot
    admin_text = (
        f"🎫 <b>Новый тикет #{ticket_id}</b>\n\n"
        f"👤 Пользователь: {full_name} (@{username})\n"
        f"🪪 Кабинет: <code>{cabinet_id}</code>\n"
        f"🆔 TG ID: <code>{message.from_user.id}</code>\n\n"
        f"💬 Сообщение:\n<i>{message.text}</i>"
    )

    from utils.keyboards import ticket_answer_kb
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_text,
                parse_mode="HTML",
                reply_markup=ticket_answer_kb(ticket_id)
            )
        except Exception:
            pass
