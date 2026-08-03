from collections.abc import Iterator
from contextlib import contextmanager

from shared.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

settings = get_settings()

# Celery-задачи выполняются синхронно, поэтому в воркере используем синхронный
# движок (psycopg), а не asyncpg: смешивать asyncio.run с retry-механикой Celery
# и управлением жизненным циклом сессии — лишняя сложность без выгоды.
sync_dsn = settings.database_url.replace("+asyncpg", "+psycopg")

engine = create_engine(sync_dsn, pool_pre_ping=True)
session_factory = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    # Единая транзакция на единицу работы: commit при успехе, rollback при ошибке.
    # Тяжёлый CPU-этап (OpenCV/OCR) сознательно выносим за пределы этого блока,
    # чтобы не держать соединение с БД открытым секундами.
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
