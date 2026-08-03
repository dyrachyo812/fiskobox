from datetime import date

from shared.models import Document, Receipt
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def summary_by_category(
    session: AsyncSession, user_id: int, start: date | None
) -> list[tuple[str | None, object, int]]:
    period = func.coalesce(Receipt.purchase_date, cast(Document.created_at, Date))
    filters = [
        Document.user_id == user_id,
        Receipt.amount.is_not(None),
    ]
    if start is not None:
        filters.append(period >= start)

    statement = (
        select(Receipt.category, func.sum(Receipt.amount), func.count())
        .join(Document, Receipt.document_id == Document.id)
        .where(*filters)
        .group_by(Receipt.category)
    )

    return list((await session.execute(statement)).all())
