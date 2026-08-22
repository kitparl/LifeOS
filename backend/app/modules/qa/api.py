from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.qa.schemas import (
    QACreate,
    QAListItem,
    QAResponse,
    QATypeCreate,
    QAUpdate,
    QAVersionResponse,
)
from app.modules.qa.service import QAService

router = APIRouter(prefix="/qa", tags=["qa"])


@router.get("/entries", response_model=list[QAListItem])
async def list_qa_entries(
    response: Response,
    search: str | None = Query(default=None),
    type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    deep_personal: bool | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    sort_by: str = Query(default="updated_at", pattern="^(created_at|updated_at)$"),
    limit: int | None = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_answer: bool = Query(default=True),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await QAService(db).list_entries(
        user.id,
        search=search,
        type_filter=type,
        tag=tag,
        deep_personal=deep_personal,
        created_from=created_from,
        created_to=created_to,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
        include_answer=include_answer,
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/types", response_model=list[str])
async def list_qa_types(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await QAService(db).list_types(user.id)


@router.post("/types", response_model=list[str], status_code=status.HTTP_201_CREATED)
async def create_qa_type(
    data: QATypeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await QAService(db).create_type(user.id, data.name)
    return await QAService(db).list_types(user.id)


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
