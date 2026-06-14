from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from database.db import AsyncSessionLocal, get_user_by_telegram_id, get_referral_count
from utils.keyboards import back_main
from config import REFERRAL_BONUS_REFERRER, REFERRAL_BONUS_NEW_USER

router = Router()


@router.callback_query(F.data == "referral_menu")
async def referral_menu(callback: CallbackQuery):
    bot: Bot = callback.bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    async with AsyncSessionLocal() as session:
        user = await get_user_by_telegram_id(session, callback.from_user.id)
        if not user:
            await callback.answer("Профиль не найден", show_alert=True)
            return
        ref_count = await get_referral_count(session, user.id)
        balance = user.balance

    ref_link = f"https://t.me/{bot_username}?start={user.referral_code}"

    text = (
        f"👥 <b>Реферальная система</b>\n\n"
        f"Приглашай друзей — получай деньги на баланс.\n\n"
        f"🎁 <b>Условия:</b>\n"
        f"   • Ты получаешь <b>{REFERRAL_BONUS_REFERRER:.0f} ₽</b> за каждого нового реферала\n"
        f"   • Новый пользователь получает <b>{REFERRAL_BONUS_NEW_USER:.0f} ₽</b> бонуса\n"
        f"   • Выплата — мгновенно на баланс в боте\n\n"
        f"📊 <b>Твоя статистика:</b>\n"
        f"   👤 Приглашено: <b>{ref_count}</b> чел.\n"
        f"   💰 Заработано: <b>{ref_count * REFERRAL_BONUS_REFERRER:.0f} ₽</b>\n"
        f"   🏦 Баланс: <b>{balance:.0f} ₽</b>\n\n"
        f"🔗 <b>Твоя реферальная ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"📋 <b>Твой реф-код:</b> <code>{user.referral_code}</code>"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_main())
    await callback.answer()
