from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from shared.models import Document, DocumentStatus, User
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.core.exceptions import ForbiddenError, NotFoundError
from backend.db.session import get_session
from backend.repositories.documentrepository import (
    apply_manual_update,
    delete_document,
    get_document_by_id,
    list_documents,
)
from backend.schemas.document import (
    DocumentDetailOut,
    DocumentListOut,
    DocumentUpdate,
    ReceiptOut,
)

router = APIRouter()


def to_detail(document: Document) -> DocumentDetailOut:
    receipt = ReceiptOut.model_validate(document.receipt) if document.receipt else None
    return DocumentDetailOut(
        id=document.id,
        status=document.status,
        created_at=document.created_at,
        receipt=receipt,
        low_quality_scan=document.low_quality_scan,
        raw_ocr_text=document.raw_ocr_text,
        image_url=f"/api/documents/{document.id}/image",
        sharpness_score=document.sharpness_score,
    )


async def require_owned_document(
    session: AsyncSession, user: User, document_id: int
) -> Document:
    document = await get_document_by_id(session, document_id)
    if document is None:
        raise NotFoundError("Документ не найден")
    if document.user_id != user.id:
        raise ForbiddenError("Нет доступа к чужому документу")
    return document


@router.get("", response_model=DocumentListOut)
async def list_user_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: DocumentStatus | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentListOut:
    documents, total = await list_documents(
        session,
        user.id,
        limit=limit,
        offset=offset,
        status=status,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )
    return DocumentListOut(items=documents, total=total, limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentDetailOut)
async def get_user_document(
    document_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentDetailOut:
    document = await require_owned_document(session, user, document_id)
    return to_detail(document)


@router.get("/{document_id}/image")
async def get_user_document_image(
    document_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    document = await require_owned_document(session, user, document_id)

    path = Path(document.image_path)
    if not path.exists():
        raise NotFoundError("Файл изображения не найден")
    return FileResponse(path)


@router.patch("/{document_id}", response_model=DocumentDetailOut)
async def update_user_document(
    document_id: int,
    payload: DocumentUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentDetailOut:
    document = await require_owned_document(session, user, document_id)

    apply_manual_update(session, document, payload.model_dump(exclude_unset=True))
    await session.commit()
    await session.refresh(document, attribute_names=["receipt"])
    return to_detail(document)


@router.delete("/{document_id}", status_code=204)
async def delete_user_document(
    document_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    document = await require_owned_document(session, user, document_id)
    image_path = await delete_document(session, document)
    await session.commit()
    if image_path:
        path = Path(image_path)
        if path.exists() and path.is_file():
            path.unlink()
