from decimal import Decimal

from pydantic import BaseModel


class CategorySummary(BaseModel):
    category: str
    amount: Decimal
    count: int


class SummaryOut(BaseModel):
    period: str
    total: Decimal
    categories: list[CategorySummary]
