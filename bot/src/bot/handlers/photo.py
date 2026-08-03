from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import Message
from shared.config import get_settings
from shared.logging import get_logger

from bot.db.session import session_factory
from bot.repositories.intake import create_document, ensure_user, find_document_by_hash
from bot.services.imagehash import compute_hash
from bot.services.publisher import enqueue_document
from bot.services.ratelimit import is_allowed

router = Router()
logger = get_logger(__name__)


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    telegram_id = message.from_user.id

    if not await is_allowed(telegram_id):
        logger.warning(
            "Превышен лимит фото", extra={"telegram_id": telegram_id, "stage": "ratelimit"}
        )
        await message.answer("Слишком много фото подряд. Подождите минуту.")
        return

    buffer = await bot.download(message.photo[-1])
    image_bytes = buffer.read()
    image_hash = compute_hash(image_bytes)

    async with session_factory() as session:
        user = await ensure_user(session, telegram_id, message.from_user.username)

        duplicate = await find_document_by_hash(session, user.id, image_hash)
        if duplicate is not None:
            await session.commit()
            logger.info(
                "Дубликат чека пропущен",
                extra={
                    "telegram_id": telegram_id,
                    "document_id": duplicate.id,
                    "stage": "dedup",
                },
            )
            await message.answer("Этот чек уже загружен, дубликат пропущен.")
            return

        settings = get_settings()
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        image_path = upload_dir / f"{image_hash}.jpg"
        image_path.write_bytes(image_bytes)

        document_id = await create_document(session, user.id, str(image_path), image_hash)
        await session.commit()

    enqueue_document(document_id)
    logger.info(
        "Задача поставлена в очередь",
        extra={"telegram_id": telegram_id, "document_id": document_id, "stage": "enqueue"},
    )
    settings = get_settings()
    parser_mode = (settings.parser_mode or "regex").strip().lower()
    if parser_mode in {"llm", "hybrid"}:
        seconds = max(30, int(settings.ollama_timeout_seconds) + 10)
        await message.answer(
            f"Чек получен, обрабатываю — это может занять до {seconds} секунд ⏳"
        )
    else:
        await message.answer("Чек получен, обрабатываю ⏳")
