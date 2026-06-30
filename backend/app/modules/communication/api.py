from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.communication.schemas import (
    SpeakingCreate,
    SpeakingResponse,
    SpeakingUpdate,
    VocabularyCreate,
    VocabularyResponse,
    VocabularyUpdate,
    WritingCreate,
    WritingResponse,
    WritingUpdate,
)
from app.modules.communication.service import CommunicationService

router = APIRouter(prefix="/communication", tags=["communication"])


@router.get("/vocabulary", response_model=list[VocabularyResponse])
async def list_vocabulary(
    search: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).list_vocabulary(user.id, search=search)


@router.post("/vocabulary", response_model=VocabularyResponse, status_code=status.HTTP_201_CREATED)
async def create_vocabulary(
    data: VocabularyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).create_vocabulary(user.id, data)


@router.get("/vocabulary/{word_id}", response_model=VocabularyResponse)
async def get_vocabulary(
    word_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).get_vocabulary(user.id, word_id)


@router.patch("/vocabulary/{word_id}", response_model=VocabularyResponse)
async def update_vocabulary(
    word_id: str,
    data: VocabularyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).update_vocabulary(user.id, word_id, data)


@router.delete("/vocabulary/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vocabulary(
    word_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await CommunicationService(db).delete_vocabulary(user.id, word_id)


@router.get("/writing", response_model=list[WritingResponse])
async def list_writing(
    category: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).list_writing(user.id, category=category)


@router.post("/writing", response_model=WritingResponse, status_code=status.HTTP_201_CREATED)
async def create_writing(
    data: WritingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).create_writing(user.id, data)


@router.get("/writing/{item_id}", response_model=WritingResponse)
async def get_writing(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).get_writing(user.id, item_id)


@router.patch("/writing/{item_id}", response_model=WritingResponse)
async def update_writing(
    item_id: str,
    data: WritingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).update_writing(user.id, item_id, data)


@router.delete("/writing/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_writing(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await CommunicationService(db).delete_writing(user.id, item_id)


@router.get("/speaking", response_model=list[SpeakingResponse])
async def list_speaking(
    category: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).list_speaking(user.id, category=category)


@router.post("/speaking", response_model=SpeakingResponse, status_code=status.HTTP_201_CREATED)
async def create_speaking(
    data: SpeakingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).create_speaking(user.id, data)


@router.get("/speaking/{item_id}", response_model=SpeakingResponse)
async def get_speaking(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).get_speaking(user.id, item_id)


@router.patch("/speaking/{item_id}", response_model=SpeakingResponse)
async def update_speaking(
    item_id: str,
    data: SpeakingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).update_speaking(user.id, item_id, data)


@router.delete("/speaking/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_speaking(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await CommunicationService(db).delete_speaking(user.id, item_id)
