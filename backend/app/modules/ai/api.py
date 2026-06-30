from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.ai.schemas import AiChatRequest, AiChatResponse, AiIndexResponse, AiStatusResponse
from app.modules.ai.service import AiService
from app.modules.auth.models import User

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=AiStatusResponse)
async def ai_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiService(db).status(user.id)


@router.post("/index", response_model=AiIndexResponse)
async def ai_index(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiService(db).index(user.id)


@router.post("/chat", response_model=AiChatResponse)
async def ai_chat(
    data: AiChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiService(db).chat(user.id, data.message)
