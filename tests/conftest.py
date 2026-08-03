import os
import shutil
import subprocess
import time
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "tests" / "fixtures"
COMPOSE_FILE = ROOT / "docker-compose.test.yml"

DOCKER_DATABASE_URL = (
    "postgresql+asyncpg://paperless_test:paperless_test@127.0.0.1:5433/paperlessbox_test"
)
LOCAL_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/paperlessbox_test"
)
DOCKER_REDIS_URL = "redis://127.0.0.1:6380/0"
LOCAL_REDIS_URL = "redis://127.0.0.1:6379/0"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _compose(args: list[str]) -> None:
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *args],
        check=True,
        cwd=ROOT,
    )


def _wait_for_db(url: str, attempts: int = 60) -> None:
    sync_url = url.replace("+asyncpg", "+psycopg")
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            engine = create_engine(sync_url, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            engine.dispose()
            return
        except Exception as error:
            last_error = error
            time.sleep(1)
    raise RuntimeError(f"Test database is not ready: {last_error}")


def _ensure_database_exists(url: str) -> None:
    sync_url = url.replace("+asyncpg", "+psycopg")
    db_name = sync_url.rsplit("/", 1)[-1]
    admin_url = sync_url.rsplit("/", 1)[0] + "/postgres"
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def test_env() -> Iterator[dict[str, str]]:
    managed_compose = False
    database_url = os.getenv("TEST_DATABASE_URL")
    redis_url = os.getenv("TEST_REDIS_URL")

    if database_url is None:
        if _docker_available():
            _compose(["up", "-d", "--wait"])
            managed_compose = True
            database_url = DOCKER_DATABASE_URL
            redis_url = redis_url or DOCKER_REDIS_URL
        else:
            database_url = LOCAL_DATABASE_URL
            redis_url = redis_url or LOCAL_REDIS_URL
    else:
        redis_url = redis_url or LOCAL_REDIS_URL

    result_backend = (
        redis_url[:-1] + "1" if redis_url.endswith("/0") else redis_url
    )

    env = {
        "DATABASE_URL": database_url,
        "REDIS_URL": redis_url,
        "CELERY_BROKER_URL": redis_url,
        "CELERY_RESULT_BACKEND": result_backend,
        "JWT_SECRET": "integration-test-secret",
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "TELEGRAM_BOT_TOKEN": "000000000:TESTTOKENFORINTEGRATIONTESTS",
        "TELEGRAM_BOT_USERNAME": "PaperlessBoxTestBot",
        "UPLOAD_DIR": str(ROOT / "tests" / ".uploads"),
        "OCR_PROVIDER": "tesseract",
        "OCR_ENGINE": "tesseract",
        "TESSERACT_LANGUAGES": "eng",
        "PARSER_MODE": "regex",
        "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
        "BLUR_VARIANCE_THRESHOLD": "5.0",
    }
    for key, value in env.items():
        os.environ[key] = value

    from shared.config.settings import get_settings

    get_settings.cache_clear()

    try:
        _ensure_database_exists(database_url)
        _wait_for_db(database_url)
    except Exception as error:
        if managed_compose:
            _compose(["down", "-v"])
        pytest.skip(f"Тестовая БД недоступна: {error}")

    yield env

    get_settings.cache_clear()
    if managed_compose:
        _compose(["down", "-v"])


@pytest.fixture(scope="session")
def prepare_fixtures(test_env: dict[str, str]) -> Path:
    script = FIXTURES_DIR / "generateReceipts.py"
    subprocess.run(["python", str(script)], check=True, cwd=ROOT)
    upload_dir = Path(test_env["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    return FIXTURES_DIR


@pytest_asyncio.fixture
async def db_engine(test_env: dict[str, str]):
    from shared.models import Base

    engine = create_async_engine(test_env["DATABASE_URL"], pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    from shared.models import User

    user = User(telegram_id=100001, username="owner")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession):
    from shared.models import User

    user = User(telegram_id=100002, username="intruder")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def owner_token(test_env: dict[str, str], test_user) -> str:
    from shared.config.settings import get_settings

    get_settings.cache_clear()
    from backend.core.security import create_access_token

    return create_access_token(str(test_user.telegram_id))


@pytest.fixture
def other_token(test_env: dict[str, str], other_user) -> str:
    from shared.config.settings import get_settings

    get_settings.cache_clear()
    from backend.core.security import create_access_token

    return create_access_token(str(other_user.telegram_id))


@pytest_asyncio.fixture
async def api_client(test_env: dict[str, str], db_engine) -> AsyncIterator[AsyncClient]:
    from shared.config.settings import get_settings

    get_settings.cache_clear()

    from backend.db import session as db_session_module
    from backend.db.session import get_session
    from backend.main import app

    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    db_session_module.engine = db_engine
    db_session_module.session_factory = factory

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sync_session_factory(test_env: dict[str, str], prepare_fixtures: Path):
    from shared.config.settings import get_settings
    from shared.models import Base

    get_settings.cache_clear()
    sync_url = test_env["DATABASE_URL"].replace("+asyncpg", "+psycopg")
    engine = create_engine(sync_url, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    import worker.db.session as worker_session

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    worker_session.engine = engine
    worker_session.session_factory = factory
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sync_session(sync_session_factory) -> Iterator[Session]:
    session = sync_session_factory()
    try:
        yield session
        session.commit()
    finally:
        session.close()
