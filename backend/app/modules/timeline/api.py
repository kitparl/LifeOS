from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.timeline.schemas import TimelineItem, TimelineSource
from app.modules.timeline.service import TimelineService

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/sources", response_model=list[TimelineSource])
async def list_sources(_: User = Depends(get_current_user)):
    return TimelineService.list_sources()


@router.get("", response_model=list[TimelineItem])
async def list_timeline(
    start: date = Query(...),
    end: date = Query(...),
    sources: list[str] | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TimelineService(db).list_items(user.id, start, end, sources)
