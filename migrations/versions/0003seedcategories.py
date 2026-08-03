"""seed default categories

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-02 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CATEGORIES = [
    (
        "Продукты",
        [
            "атб",
            "сільпо",
            "сильпо",
            "silpo",
            "фора",
            "fora",
            "ашан",
            "auchan",
            "novus",
            "новус",
            "varus",
            "варто",
            "metro",
            "метро",
            "пятерочка",
            "перекресток",
            "магнит",
            "продукт",
            "супермаркет",
            "маркет",
        ],
    ),
    (
        "Кафе",
        [
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
            "pizza",
            "піца",
            "пицца",
            "автокафе",
        ],
    ),
    (
        "Электроника",
        [
            "dns",
            "днс",
            "comfy",
            "комфі",
            "комфи",
            "алло",
            "allo",
            "rozetka",
            "розетка",
            "sony",
            "samsung",
            "apple",
            "xiaomi",
            "ноутбук",
            "телефон",
            "наушник",
            "техник",
        ],
    ),
    (
        "Транспорт",
        [
            "uber",
            "bolt",
            "uklon",
            "уклон",
            "укрзализныця",
            "укрзалізниця",
            "taxi",
            "такси",
            "заправк",
            "okko",
            "окко",
            "wog",
            "вок",
            "shell",
        ],
    ),
    (
        "Аптека",
        [
            "аптек",
            "pharmacy",
            "анц",
            "подорожник",
            "фармац",
            "ліки",
            "лекарств",
        ],
    ),
    (
        "Одежда",
        [
            "zara",
            "h&m",
            "reserved",
            "одежд",
            "взутт",
            "обув",
            "спортмастер",
            "intertop",
        ],
    ),
    (
        "Дом и ремонт",
        [
            "епіцентр",
            "эпицентр",
            "epicentr",
            "леруа",
            "leroymerlin",
            "строй",
            "ремонт",
            "мебель",
        ],
    ),
]


def upgrade() -> None:
    categories = sa.table(
        "categories",
        sa.column("name", sa.String),
        sa.column("keywords", sa.ARRAY(sa.String)),
    )
    op.bulk_insert(
        categories,
        [{"name": name, "keywords": keywords} for name, keywords in CATEGORIES],
    )


def downgrade() -> None:
    names = ", ".join(f"'{name}'" for name, _keywords in CATEGORIES)
    op.execute(f"DELETE FROM categories WHERE name IN ({names})")
