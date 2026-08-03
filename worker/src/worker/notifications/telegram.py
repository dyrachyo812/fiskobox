import asyncio

from aiogram import Bot
from shared.config import get_settings
from shared.logging import get_logger

logger = get_logger(__name__)


def notify_result(chat_id: int, text: str) -> bool:
    try:
        asyncio.run(send_message(chat_id, text))
        logger.info(
            "Сообщение отправлено в Telegram",
            extra={"chat_id": chat_id, "stage": "notify"},
        )
        return True
    except Exception as error:
        logger.exception(
            "Не удалось отправить сообщение в Telegram: %s",
            error,
            extra={"chat_id": chat_id, "stage": "notify"},
        )
        return False


async def send_message(chat_id: int, text: str) -> None:
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    finally:
        await bot.session.close()
