from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.session import session_factory
from bot.repositories.intake import ensure_user
from bot.services.linkcode import create_link_code

router = Router()


@router.message(Command("link"))
async def handle_link(message: Message) -> None:
    # Гарантируем, что пользователь есть в БД (код привязки указывает именно на него).
    async with session_factory() as session:
        await ensure_user(session, message.from_user.id, message.from_user.username)
        await session.commit()

    code = await create_link_code(message.from_user.id)
    await message.answer(
        f"Код для входа в веб-панель: <b>{code}</b>\n"
        "Введите его на сайте в течение 10 минут.",
        parse_mode="HTML",
    )
