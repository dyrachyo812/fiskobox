from fastapi import APIRouter, Depends
from shared.models import User
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user
from backend.db.session import get_session
from backend.repositories.categoryrepository import list_categories
from backend.schemas.category import CategoryListOut, CategoryOut

router = APIRouter()


@router.get("", response_model=CategoryListOut)
async def get_categories(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CategoryListOut:
    del user
    categories = await list_categories(session)
    return CategoryListOut(items=[CategoryOut.model_validate(item) for item in categories])
