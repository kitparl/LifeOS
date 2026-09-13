from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import PublicUserResponse
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search", response_model=list[PublicUserResponse])
async def search_users(
    response: Response,
    q: str = Query(min_length=1, max_length=120),
    limit: int = Query(default=25, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    results, total = await service.search_users(
        q, limit=limit, offset=offset, include_email=bool(user.is_admin)
    )
    response.headers["X-Total-Count"] = str(total)
    return [PublicUserResponse.model_validate(u) for u in results]
