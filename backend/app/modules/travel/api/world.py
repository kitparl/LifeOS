from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.travel.schemas.places import Marker
from app.modules.travel.schemas.world import WorldOverview
from app.modules.travel.services.world_service import WorldService

router = APIRouter()


@router.get("/markers", response_model=list[Marker])
async def list_markers(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Every layer (places, trips, adventures, photos) in one lightweight call; the client toggles layers."""
    return await WorldService(db).markers(user.id)


@router.get("/world", response_model=WorldOverview)
async def my_world(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await WorldService(db).overview(user.id)
