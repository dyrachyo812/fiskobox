import secrets

from redis.asyncio import Redis
from shared.config import get_settings

settings = get_settings()

CODE_PREFIX = "linkcode:"
CODE_TTL_SECONDS = 600

# Одноразовые коды храним в Redis, а не в БД: им нужен TTL и атомарное «прочитал-и-удалил»,
# а таблица под эфемерные коды — лишняя миграция и мусор. Redis общий для бота и backend,
# поэтому backend сможет обменять код на JWT (эндпоинт добавим на шаге FastAPI).
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def create_link_code(telegram_id: int) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    await redis_client.set(f"{CODE_PREFIX}{code}", telegram_id, ex=CODE_TTL_SECONDS)
    return code
