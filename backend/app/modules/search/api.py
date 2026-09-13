from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.search.schemas import SearchResponse
from app.modules.search.service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def global_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=25, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SearchService(db).search(user.id, q, limit=limit, offset=offset)


@router.get("/semantic", response_model=SearchResponse)
async def semantic_search(
    q: str = Query(min_length=1),
    limit: int = Query(default=25, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SearchService(db).semantic_search(user.id, q, limit=limit, offset=offset)
