from backend.core.exceptions import InvalidLinkCodeError
from backend.services.redisclient import redis_client

CODE_PREFIX = "linkcode:"


async def consume_link_code(code: str) -> int:
    telegram_id = await redis_client.getdel(f"{CODE_PREFIX}{code}")
    if telegram_id is None:
        raise InvalidLinkCodeError()
    return int(telegram_id)
