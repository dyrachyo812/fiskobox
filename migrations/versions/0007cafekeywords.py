"""expand cafe category keywords

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-03 02:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CAFE_KEYWORDS = [
    "mcdonald",
    "mcdonalds",
    "макдональдз",
    "макдональдс",
    "starbucks",
    "старбакс",
    "kfc",
    "кафе",
    "ресторан",
    "закусочн",
    "coffee",
    "кофе",
    "кава",
    "капучино",
    "капуччіно",
    "капуччино",
    "cappuccino",
    "еспресо",
    "espresso",
    "латте",
    "стейк",
    "салат",
    "резонанс",
    "resonance",
    "pizza",
    "піца",
    "пицца",
    "автокафе",
    "pizza day",
    "піца дей",
    "бургер",
    "sushi",
    "суши",
    "пекарн",
    "bakery",
    "domino",
    "доміно",
    "lviv croissants",
    "арома кава",
]


def upgrade() -> None:
    categories = sa.table(
        "categories",
        sa.column("name", sa.String),
        sa.column("keywords", sa.ARRAY(sa.String)),
    )
    op.execute(
        categories.update()
        .where(categories.c.name == "Кафе")
        .values(keywords=CAFE_KEYWORDS)
    )


def downgrade() -> None:
    pass
