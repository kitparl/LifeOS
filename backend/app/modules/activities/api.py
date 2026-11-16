from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.activities.schemas import ActivityDetail, ActivitySeriesResponse
from app.modules.activities.service import ActivityService
from app.modules.auth.models import User

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("/{activity_id}", response_model=ActivityDetail)
async def get_activity(
    activity_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ActivityService(db).get_activity(user.id, activity_id)


@router.get("/{activity_id}/series", response_model=ActivitySeriesResponse)
async def get_activity_series(
    activity_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ActivityService(db).get_series(user.id, activity_id)
