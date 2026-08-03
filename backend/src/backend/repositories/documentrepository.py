from datetime import date

from shared.models import Document, DocumentStatus, Receipt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


def build_filters(
    user_id: int,
    status: DocumentStatus | None,
    category: str | None,
    date_from: date | None,
    date_to: date | None,
) -> list:
    filters = [Document.user_id == user_id]
    if status is not None:
        filters.append(Document.status == status)
    if category is not None:
        filters.append(Receipt.category == category)
    if date_from is not None:
        filters.append(Receipt.purchase_date >= date_from)
    if date_to is not None:
        filters.append(Receipt.purchase_date <= date_to)
    return filters


async def list_documents(
    session: AsyncSession,
    user_id: int,
    limit: int,
    offset: int,
    status: DocumentStatus | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[Document], int]:
    filters = build_filters(user_id, status, category, date_from, date_to)
    needs_receipt = any(
        value is not None for value in (category, date_from, date_to)
    )

    count_statement = select(func.count()).select_from(Document)
    if needs_receipt:
        count_statement = count_statement.join(
            Receipt, Receipt.document_id == Document.id
        )
    total = await session.scalar(count_statement.where(*filters))

    statement = (
        select(Document)
        .where(*filters)
        .options(selectinload(Document.receipt))
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if needs_receipt:
        statement = statement.join(Receipt, Receipt.document_id == Document.id)

    documents = list(await session.scalars(statement))
    return documents, total or 0


async def get_document_by_id(
    session: AsyncSession, document_id: int
) -> Document | None:
    statement = (
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.receipt))
    )
    return await session.scalar(statement)


async def get_document(
    session: AsyncSession, user_id: int, document_id: int
) -> Document | None:
    document = await get_document_by_id(session, document_id)
    if document is None or document.user_id != user_id:
        return None
    return document


def apply_manual_update(session: AsyncSession, document: Document, data: dict) -> None:
    receipt = document.receipt
    if receipt is None:
        receipt = Receipt(document_id=document.id)
        document.receipt = receipt
    for field in ("amount", "currency", "merchant_name", "purchase_date", "category"):
        if field in data:
            setattr(receipt, field, data[field])
    receipt.is_manually_corrected = True
    session.add(receipt)


async def delete_document(session: AsyncSession, document: Document) -> str | None:
    image_path = document.image_path
    await session.delete(document)
    return image_path
