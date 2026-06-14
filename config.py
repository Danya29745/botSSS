import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Список Telegram ID администраторов (через запятую в .env)
ADMIN_IDS: list[int] = [
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

# ── База данных ───────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///halvex.db")

# ── Реферальная система ───────────────────────────────────
# Бонус рефереру (в рублях/единицах баланса)
REFERRAL_BONUS_REFERRER: float = float(os.getenv("REFERRAL_BONUS_REFERRER", "50"))
# Бонус новому пользователю
REFERRAL_BONUS_NEW_USER: float = float(os.getenv("REFERRAL_BONUS_NEW_USER", "30"))

# ── 3x-UI панель (заполнить позже) ───────────────────────
XUI_HOST: str = os.getenv("XUI_HOST", "")
XUI_USERNAME: str = os.getenv("XUI_USERNAME", "")
XUI_PASSWORD: str = os.getenv("XUI_PASSWORD", "")

# ── Платёжная система (заполнить позже) ──────────────────
PAYMENT_TOKEN: str = os.getenv("PAYMENT_TOKEN", "")

# ── Тарифы подписки (дней → цена) ────────────────────────
PLANS: dict[str, dict] = {
    "1m":  {"label": "1 месяц",  "days": 30,  "price": 199},
    "3m":  {"label": "3 месяца", "days": 90,  "price": 499},
    "6m":  {"label": "6 месяцев","days": 180, "price": 899},
    "12m": {"label": "1 год",    "days": 365, "price": 1499},
}
