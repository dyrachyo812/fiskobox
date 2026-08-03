from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Привет! Пришлите фото чека — распознаю сумму, дату, продавца и категорию.\n\n"
        "/link — привязать веб-панель\n"
        "/stats — траты за текущий месяц"
    )
