from shared.models import Category
from sqlalchemy import select
from sqlalchemy.orm import Session


def load_categories(session: Session) -> list[Category]:
    # Справочник категорий небольшой, поэтому грузим целиком и матчим в памяти —
    # это дешевле и гибче, чем строить SQL-запрос по массиву keywords на каждый чек.
    return list(session.scalars(select(Category)))
