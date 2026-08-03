from redis.asyncio import Redis
from shared.config import get_settings

settings = get_settings()

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def is_allowed(telegram_id: int) -> bool:
    # Счётчик с TTL на окно: первый запрос в окне выставляет expire, дальше только INCR.
    # Атомарный INCR в Redis корректно работает и при нескольких инстансах бота.
    key = f"ratelimit:photo:{telegram_id}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, settings.photo_rate_window_seconds)
    return count <= settings.photo_rate_limit
