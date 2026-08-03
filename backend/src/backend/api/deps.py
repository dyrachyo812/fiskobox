from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from shared.models import User
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import AuthError
from backend.core.security import decode_access_token
from backend.db.session import get_session
from backend.repositories.userrepository import get_by_telegram_id

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise AuthError()

    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise AuthError()

    user = await get_by_telegram_id(session, int(subject))
    if user is None:
        raise AuthError("Пользователь не найден")
    return user
