import uuid
import random
import string
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, BigInteger, String, Float,
    DateTime, Boolean, Text, ForeignKey, select
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship

from config import DATABASE_URL


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── Модели ────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=True)
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

    support_tickets = relationship("SupportTicket", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_answered = Column(Boolean, default=False)
    answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="support_tickets")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(256), nullable=True)
    status = Column(String(32), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="payments")


# ── Хелперы ───────────────────────────────────────────────

def _generate_cabinet_id() -> str:
    return "HVX-" + "".join(random.choices(string.digits, k=6))


def _generate_referral_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── CRUD ──────────────────────────────────────────────────

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str | None,
    ref_code: str | None = None,
) -> tuple["User", bool]:

    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user:
        return user, False

    while True:
        cabinet_id = _generate_cabinet_id()
        exists = await session.execute(
            select(User).where(User.cabinet_id == cabinet_id)
        )
        if not exists.scalar_one_or_none():
            break

    while True:
        referral_code = _generate_referral_code()
        exists = await session.execute(
            select(User).where(User.referral_code == referral_code)
        )
        if not exists.scalar_one_or_none():
            break

    referrer_id = None

    if ref_code:
        res = await session.execute(
            select(User).where(User.referral_code == ref_code)
        )
        referrer = res.scalar_one_or_none()

        if referrer and referrer.telegram_id != telegram_id:
            referrer_id = referrer.id

    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        cabinet_id=cabinet_id,
        referral_code=referral_code,
        referred_by=referrer_id,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user, True


async def get_user_by_telegram_id(
    session: AsyncSession,
    telegram_id: int
) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_cabinet_id(
    session: AsyncSession,
    cabinet_id: str
) -> User | None:
    result = await session.execute(
        select(User).where(User.cabinet_id == cabinet_id)
    )
    return result.scalar_one_or_none()


async def get_referral_count(session: AsyncSession, user_id: int) -> int:
    from sqlalchemy import func

    result = await session.execute(
        select(func.count()).where(User.referred_by == user_id)
    )

    return result.scalar() or 0


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).order_by(User.created_at.desc())
    )
    return list(result.scalars().all())


async def get_new_users_since(
    session: AsyncSession,
    since: datetime
) -> list[User]:
    result = await session.execute(
        select(User)
        .where(User.created_at >= since)
        .order_by(User.created_at.desc())
    )
    return list(result.scalars().all())


async def create_support_ticket(
    session: AsyncSession,
    user_id: int,
    message: str
) -> SupportTicket:
    ticket = SupportTicket(
        user_id=user_id,
        message=message
    )

    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)

    return ticket


async def get_open_tickets(
    session: AsyncSession
) -> list[SupportTicket]:
    result = await session.execute(
        select(SupportTicket)
        .where(SupportTicket.is_answered == False)
        .order_by(SupportTicket.created_at.asc())
    )

    return list(result.scalars().all())
