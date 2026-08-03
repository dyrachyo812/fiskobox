from datetime import date

from shared.models import Document, Receipt
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def summary_by_category(
    session: AsyncSession, user_id: int, start: date
) -> list[tuple[str | None, object, int]]:
    period = func.coalesce(Receipt.purchase_date, cast(Document.created_at, Date))

    statement = (
        select(Receipt.category, func.sum(Receipt.amount), func.count())
        .join(Document, Receipt.document_id == Document.id)
        .where(
            Document.user_id == user_id,
            Receipt.amount.is_not(None),
            period >= start,
        )
        .group_by(Receipt.category)
    )

    return list((await session.execute(statement)).all())
