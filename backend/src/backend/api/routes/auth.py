from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import create_access_token
from backend.db.session import get_session
from backend.repositories.userrepository import get_or_create
from backend.schemas.auth import LinkTelegramRequest, TokenResponse
from backend.services.authservice import consume_link_code

router = APIRouter()


@router.post("/link-telegram", response_model=TokenResponse)
async def link_telegram(
    payload: LinkTelegramRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    telegram_id = await consume_link_code(payload.code)
    await get_or_create(session, telegram_id)
    await session.commit()

    token = create_access_token(str(telegram_id))
    return TokenResponse(access_token=token)
