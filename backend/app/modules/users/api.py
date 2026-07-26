from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import PublicUserResponse
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search", response_model=list[PublicUserResponse])
async def search_users(
    q: str = Query(min_length=1, max_length=120),
    limit: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    results = await service.search_users(q, limit=limit, include_email=bool(user.is_admin))
    return [PublicUserResponse.model_validate(u) for u in results]
