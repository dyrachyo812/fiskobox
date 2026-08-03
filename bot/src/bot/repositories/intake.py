from shared.models import Document, DocumentStatus, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def ensure_user(
    session: AsyncSession, telegram_id: int, username: str | None
) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.flush()
    return user


async def find_document_by_hash(
    session: AsyncSession, user_id: int, image_hash: str
) -> Document | None:
    return await session.scalar(
        select(Document)
        .where(Document.user_id == user_id, Document.image_hash == image_hash)
        .order_by(Document.id.desc())
    )


async def create_document(
    session: AsyncSession, user_id: int, image_path: str, image_hash: str
) -> int:
    document = Document(
        user_id=user_id,
        image_path=image_path,
        image_hash=image_hash,
        status=DocumentStatus.pending,
    )
    session.add(document)
    await session.flush()
    return document.id
