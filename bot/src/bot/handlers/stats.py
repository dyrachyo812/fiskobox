from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.session import session_factory
from bot.repositories.stats import monthly_summary
from bot.services.statsmessage import format_stats

router = Router()


@router.message(Command("stats"))
async def handle_stats(message: Message) -> None:
    async with session_factory() as session:
        summary = await monthly_summary(session, message.from_user.id)
    await message.answer(format_stats(summary))
