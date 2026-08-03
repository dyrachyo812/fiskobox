import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.types import BotCommand
from aiogram.utils.token import TokenValidationError
from shared.config import get_settings
from shared.logging import configure_logging

from bot.handlers import link, photo, start, stats

logger = logging.getLogger(__name__)


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="О боте"),
            BotCommand(command="link", description="Привязать веб-панель"),
            BotCommand(command="stats", description="Траты за месяц"),
        ]
    )


async def run_bot(token: str) -> None:
    bot = Bot(token=token)
    dispatcher = Dispatcher()
    dispatcher.include_router(start.router)
    dispatcher.include_router(link.router)
    dispatcher.include_router(stats.router)
    dispatcher.include_router(photo.router)
    await setup_commands(bot)
    await dispatcher.start_polling(bot)


async def main() -> None:
    configure_logging()
    settings = get_settings()

    while True:
        try:
            await run_bot(settings.telegram_bot_token)
            return
        except (TokenValidationError, TelegramUnauthorizedError) as error:
            logger.error(
                "Невалидный TELEGRAM_BOT_TOKEN (%s). Укажите токен бота в .env. "
                "Повтор через 30 секунд.",
                error,
            )
            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
