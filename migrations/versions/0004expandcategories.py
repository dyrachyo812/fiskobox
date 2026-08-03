"""expand category keywords

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-02 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
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
            "гипермаркет",
            "маркет",
            "spar",
            "спар",
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
            "м.видео",
            "мвидео",
            "mvideo",
            "ситилинк",
            "citilink",
            "eldorado",
            "эльдорадо",
            "foxtrot",
            "фокстрот",
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
            "азс",
            "okko",
            "окко",
            "wog",
            "вок",
            "shell",
            "таврида",
            "petrol",
            "петролиум",
            "сокар",
            "socar",
            "upg",
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
            "dior",
            "gucci",
            "louis vuitton",
            "prada",
            "chanel",
            "hermes",
            "бутик",
            "boutique",
            "shoes",
            "сумка",
            "luxury",
            "люкс",
            "massimo dutti",
            "bershka",
            "pull&bear",
            "nike",
            "adidas",
            "new balance",
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
    connection = op.get_bind()
    for name, keywords in CATEGORIES:
        updated = connection.execute(
            categories.update()
            .where(categories.c.name == name)
            .values(keywords=keywords)
        )
        if updated.rowcount == 0:
            connection.execute(
                categories.insert().values(name=name, keywords=keywords)
            )


def downgrade() -> None:
    pass
