from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.coaches.schemas import COACH_TYPES, CoachChatRequest, CoachChatResponse
from app.modules.coaches.service import CoachesService

router = APIRouter(prefix="/coaches", tags=["coaches"])


@router.get("/types")
async def list_coach_types():
    return {"types": list(COACH_TYPES)}


@router.post("/{coach_type}/chat", response_model=CoachChatResponse)
async def coach_chat(
    coach_type: str,
    data: CoachChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CoachesService(db).chat(user.id, coach_type, data.message)
