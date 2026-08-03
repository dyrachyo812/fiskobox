from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from shared.models import User
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_session
from backend.repositories.analyticsrepository import summary_by_category
from backend.schemas.analytics import CategorySummary, SummaryOut
from backend.services.period import period_start

router = APIRouter()


@router.get("/summary", response_model=SummaryOut)
async def summary(
    period: str = Query("month", pattern="^(week|month|year)$"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SummaryOut:
    rows = await summary_by_category(session, user.id, period_start(period))

    categories = [
        CategorySummary(
            category=category or "Без категории",
            amount=amount,
            count=count,
        )
        for category, amount, count in rows
    ]
    total = sum((item.amount for item in categories), Decimal(0))
    return SummaryOut(period=period, total=total, categories=categories)
