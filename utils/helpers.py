from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def fmt_date(dt: datetime | None) -> str:
    if dt is None:
        return "нет"
    return dt.strftime("%d.%m.%Y %H:%M")


def sub_status(until: datetime | None) -> str:
    if until is None:
        return "❌ Нет подписки"
    now = utcnow()
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    if until > now:
        days = (until - now).days
        return f"✅ Активна ещё {days} дн. (до {until.strftime('%d.%m.%Y')})"
    return "⏰ Истекла"
