from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.qa.schemas import QACreate, QAListItem, QAResponse, QAUpdate, QAVersionResponse
from app.modules.qa.service import QAService

router = APIRouter(prefix="/qa", tags=["qa"])


@router.get("/entries", response_model=list[QAListItem])
async def list_qa_entries(
    search: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await QAService(db).list_entries(user.id, search=search)


@router.post("/entries", response_model=QAResponse, status_code=status.HTTP_201_CREATED)
async def create_qa_entry(
    data: QACreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await QAService(db).create_entry(user.id, data)


@router.get("/entries/{entry_id}", response_model=QAResponse)
async def get_qa_entry(
    entry_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await QAService(db).get_entry(user.id, entry_id)


@router.patch("/entries/{entry_id}", response_model=QAResponse)
async def update_qa_entry(
    entry_id: str,
    data: QAUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await QAService(db).update_entry(user.id, entry_id, data)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_qa_entry(
    entry_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await QAService(db).delete_entry(user.id, entry_id)


@router.get("/entries/{entry_id}/versions", response_model=list[QAVersionResponse])
async def list_qa_versions(
    entry_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await QAService(db).list_versions(user.id, entry_id)
