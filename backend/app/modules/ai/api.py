from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.ai.schemas import (
    AiChatRequest,
    AiChatResponse,
    AiIndexResponse,
    AiSettings,
    AiStatusResponse,
    UseCaseHistoryItem,
    UseCaseModelUpdate,
    UseCaseResponse,
)
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


@router.get("/use-cases", response_model=list[UseCaseResponse])
async def list_use_cases(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiService(db).list_use_cases(user.id)


@router.put("/use-cases/{use_case}/model", response_model=UseCaseResponse)
async def set_use_case_model(
    use_case: str,
    data: UseCaseModelUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiService(db).set_use_case_model(
        user.id, use_case, data.provider, data.model, custom=data.custom
    )


@router.get("/use-cases/{use_case}/history", response_model=list[UseCaseHistoryItem])
async def get_use_case_history(
    use_case: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiService(db).get_use_case_history(user.id, use_case)


@router.get("/settings", response_model=AiSettings)
async def get_ai_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiService(db).get_ai_settings(user.id)


@router.put("/settings", response_model=AiSettings)
async def save_ai_settings(
    data: AiSettings,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AiService(db).save_ai_settings(user.id, data)
