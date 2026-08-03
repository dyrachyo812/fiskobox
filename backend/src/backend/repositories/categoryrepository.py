from shared.models import Category
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def list_categories(session: AsyncSession) -> list[Category]:
    result = await session.scalars(select(Category).order_by(Category.name))
    return list(result)
