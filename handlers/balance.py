from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.db import AsyncSessionLocal, get_user_by_telegram_id
from utils.keyboards import topup_amounts, back_main, confirm_payment
from utils.states import TopupStates

router = Router()


@router.callback_query(F.data == "balance_topup")
async def show_topup(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        balance = user.balance if user else 0

    text = (
        f"💳 <b>Пополнение баланса</b>\n\n"
        f"💰 Текущий баланс: <b>{balance:.0f} ₽</b>\n\n"
        f"Выберите сумму пополнения:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=topup_amounts())
    await callback.answer()


@router.callback_query(F.data.startswith("topup_") & ~F.data.startswith("topup_custom"))
async def select_topup_amount(callback: CallbackQuery):
    amount = int(callback.data.split("_")[1])
    text = (
        f"💳 <b>Подтверждение оплаты</b>\n\n"
        f"Сумма: <b>{amount} ₽</b>\n\n"
        f"⚠️ После нажатия «Оплатить» вы будете перенаправлены на страницу оплаты."
    )
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=confirm_payment(amount, "balance")
    )
    await callback.answer()


@router.callback_query(F.data == "topup_custom")
async def topup_custom_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TopupStates.custom_amount)
    await callback.message.edit_text(
        "✏️ Введите сумму пополнения (минимум 50 ₽):",
        reply_markup=back_main()
    )
    await callback.answer()


@router.message(TopupStates.custom_amount)
async def topup_custom_amount(message: Message, state: FSMContext):
    await state.clear()
    try:
        amount = int(message.text.strip())
        if amount < 50:
            await message.answer("❌ Минимальная сумма — 50 ₽.", reply_markup=back_main())
            return
    except ValueError:
        await message.answer("❌ Введите корректное число.", reply_markup=back_main())
        return

    text = (
        f"💳 <b>Подтверждение оплаты</b>\n\n"
        f"Сумма: <b>{amount} ₽</b>\n\n"
        f"⚠️ После нажатия «Оплатить» вы будете перенаправлены на страницу оплаты."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=confirm_payment(amount, "balance"))


@router.callback_query(F.data.startswith("confirm_pay_balance_"))
async def confirm_pay_balance(callback: CallbackQuery):
    # TODO: интеграция с платёжной системой
    # После успешной оплаты начислять на баланс
    amount = int(callback.data.split("_")[-1])
    await callback.answer(
        f"🔧 Платёжная система будет подключена позже.\n"
        f"Сумма: {amount} ₽",
        show_alert=True
    )
