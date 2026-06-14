from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from database.db import AsyncSessionLocal, get_or_create_user, get_user_by_telegram_id
from utils.keyboards import main_menu, back_main
from utils.helpers import sub_status, fmt_date
from config import REFERRAL_BONUS_REFERRER, REFERRAL_BONUS_NEW_USER, ADMIN_IDS

router = Router()

WELCOME_TEXT = """
⚡️ <b>HalvexVPN</b>

Не обещаем сказки — даём инструмент.

🔒 Протоколы: VLESS + Reality / WireGuard
🌍 Серверы в EU, NL, DE, FI
📵 Без логов. Без компромиссов.
⚙️ Работает там, где другие сдаются.

Твой кабинет создан. Подключайся.
"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split()
    ref_code = args[1] if len(args) > 1 else None

    async with AsyncSessionLocal() as session:
        user, is_new = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            ref_code=ref_code,
        )

        # Начисляем бонусы по рефералке
        if is_new and user.referred_by:
            from sqlalchemy import select
            from database.db import User
            res = await session.execute(
                select(User).where(User.id == user.referred_by)
            )
            referrer = res.scalar_one_or_none()
            if referrer:
                referrer.balance += REFERRAL_BONUS_REFERRER
                user.balance += REFERRAL_BONUS_NEW_USER
                await session.commit()

                # Уведомляем реферера
                try:
                    from aiogram import Bot
                    bot: Bot = message.bot
                    await bot.send_message(
                        referrer.telegram_id,
                        f"🎉 По вашей реф-ссылке зарегистрировался новый пользователь!\n"
                        f"💰 Вам начислено <b>+{REFERRAL_BONUS_REFERRER} ₽</b> на баланс.",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass

        cabinet = user.cabinet_id
        greeting = "👋 С возвращением" if not is_new else "👋 Добро пожаловать"

    text = (
        f"{greeting}, <b>{message.from_user.first_name}</b>!\n\n"
        f"{WELCOME_TEXT}\n"
        f"🪪 ID кабинета: <code>{cabinet}</code>"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=main_menu())


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        cabinet = user.cabinet_id if user else "—"

    text = (
        f"⚡️ <b>HalvexVPN</b> — Главное меню\n\n"
        f"🪪 ID кабинета: <code>{cabinet}</code>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "my_profile")
async def my_profile(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.answer("Профиль не найден", show_alert=True)
            return

        from database.db import get_referral_count
        ref_count = await get_referral_count(session, user.id)

    text = (
        f"👤 <b>Мой профиль</b>\n\n"
        f"🪪 ID кабинета: <code>{user.cabinet_id}</code>\n"
        f"💰 Баланс: <b>{user.balance:.0f} ₽</b>\n"
        f"📡 Подписка: {sub_status(user.subscription_until)}\n"
        f"👥 Рефералов: <b>{ref_count}</b>\n"
        f"📅 В системе с: {fmt_date(user.created_at)}"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_main())
    await callback.answer()
