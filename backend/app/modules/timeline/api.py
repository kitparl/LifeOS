from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.timeline.schemas import TimelineItem
from app.modules.timeline.service import TimelineService

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("", response_model=list[TimelineItem])
async def list_timeline(
    response: Response,
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await TimelineService(db).list_events(user.id, limit=limit, offset=offset)
    response.headers["X-Total-Count"] = str(total)
    return items
