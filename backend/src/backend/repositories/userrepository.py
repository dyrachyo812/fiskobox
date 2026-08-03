from shared.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    return await session.scalar(select(User).where(User.telegram_id == telegram_id))


async def get_or_create(
    session: AsyncSession, telegram_id: int, username: str | None = None
) -> User:
    user = await get_by_telegram_id(session, telegram_id)
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.flush()
    return user
