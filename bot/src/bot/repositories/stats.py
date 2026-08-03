from datetime import date
from decimal import Decimal

from shared.models import Document, Receipt, User
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def monthly_summary(session: AsyncSession, telegram_id: int) -> dict:
    month_start = date.today().replace(day=1)

    # Дата траты берётся из чека, а если OCR её не нашёл — из даты загрузки документа,
    # чтобы расход всё равно попал в статистику (coalesce на стороне БД).
    period = func.coalesce(Receipt.purchase_date, cast(Document.created_at, Date))

    statement = (
        select(Receipt.category, func.sum(Receipt.amount))
        .join(Document, Receipt.document_id == Document.id)
        .join(User, Document.user_id == User.id)
        .where(User.telegram_id == telegram_id)
        .where(Receipt.amount.is_not(None))
        .where(period >= month_start)
        .group_by(Receipt.category)
    )

    rows = (await session.execute(statement)).all()
    by_category = [(category or "Без категории", amount) for category, amount in rows]
    total = sum((amount for _, amount in by_category), Decimal(0))
    return {"month": month_start, "total": total, "by_category": by_category}
