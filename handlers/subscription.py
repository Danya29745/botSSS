from datetime import timedelta, timezone
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.db import AsyncSessionLocal, get_user_by_telegram_id
from utils.keyboards import plans_keyboard, back_main, confirm_payment
from utils.helpers import sub_status, utcnow
from config import PLANS

router = Router()


@router.callback_query(F.data == "subscription_extend")
async def show_plans(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        balance = user.balance if user else 0
        sub = sub_status(user.subscription_until if user else None)

    text = (
        f"🔄 <b>Продление подписки</b>\n\n"
        f"📡 Текущий статус: {sub}\n"
        f"💰 Ваш баланс: <b>{balance:.0f} ₽</b>\n\n"
        f"Выберите тариф:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=plans_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("plan_"))
async def select_plan(callback: CallbackQuery):
    key = callback.data.split("_", 1)[1]
    plan = PLANS.get(key)
    if not plan:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        balance = user.balance if user else 0

    enough = balance >= plan["price"]
    text = (
        f"📦 <b>{plan['label']}</b>\n\n"
        f"💵 Стоимость: <b>{plan['price']} ₽</b>\n"
        f"💰 Ваш баланс: <b>{balance:.0f} ₽</b>\n"
        f"{'✅ Достаточно средств' if enough else '❌ Недостаточно средств — пополните баланс'}"
    )
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=confirm_payment(plan["price"], f"sub_{key}") if enough else back_main()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_pay_sub_"))
async def confirm_subscription(callback: CallbackQuery):
    parts = callback.data.split("_")
    # confirm_pay_sub_1m_199  →  key=1m, price=199
    key = parts[3]
    plan = PLANS.get(key)
    if not plan:
        await callback.answer("Тариф не найден", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user or user.balance < plan["price"]:
            await callback.answer("❌ Недостаточно средств", show_alert=True)
            return

        user.balance -= plan["price"]
        now = utcnow()
        current = user.subscription_until
        if current and current.replace(tzinfo=timezone.utc) > now:
            base = current.replace(tzinfo=timezone.utc)
        else:
            base = now
        user.subscription_until = base + timedelta(days=plan["days"])
        await session.commit()

    await callback.message.edit_text(
        f"✅ <b>Подписка активирована!</b>\n\n"
        f"📦 Тариф: {plan['label']}\n"
        f"📅 Активна до: {user.subscription_until.strftime('%d.%m.%Y')}\n\n"
        f"🔧 Конфигурация для подключения будет добавлена после интеграции с панелью.",
        parse_mode="HTML",
        reply_markup=back_main()
    )
    await callback.answer()
