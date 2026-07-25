from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.preferences.schemas import PreferenceListItem, PreferenceResponse, PreferenceValueUpdate
from app.modules.preferences.service import PreferenceService

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=list[PreferenceListItem])
async def list_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PreferenceService(db).list_preferences(user.id)


@router.get("/{key}", response_model=PreferenceResponse)
async def get_preference(
    key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PreferenceService(db).get_preference(user.id, key)


@router.put("/{key}", response_model=PreferenceResponse)
async def put_preference(
    key: str,
    data: PreferenceValueUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await PreferenceService(db).put_preference(user.id, key, data.value)
