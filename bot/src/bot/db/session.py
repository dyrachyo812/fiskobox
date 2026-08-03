from shared.config import get_settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

settings = get_settings()

# Бот асинхронный (aiogram), поэтому и доступ к БД делаем через async-движок.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)
