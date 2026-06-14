# Исправленный db.py
# ВАЖНО: это шаблон на основе предоставленного фрагмента.
# Если ваш исходный db.py отличается, могут потребоваться дополнительные правки.

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(64))
    full_name = Column(String(128))
    cabinet_id = Column(String(12), unique=True, nullable=False)
    referral_code = Column(String(8), unique=True, nullable=False)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    balance = Column(Float, default=0.0)
    subscription_until = Column(DateTime, nullable=True)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    referrer_user = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[referred_by],
        back_populates="referrals"
    )

    referrals = relationship(
        "User",
        back_populates="referrer_user"
    )
