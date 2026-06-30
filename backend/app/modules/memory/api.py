from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.memory.schemas import MemoryCreate, MemoryResponse, MemorySummary, MemoryUpdate
from app.modules.memory.service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/items", response_model=list[MemoryResponse])
async def list_memory(
    category: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MemoryService(db).list_items(user.id, category)


@router.get("/summary", response_model=MemorySummary)
async def memory_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MemoryService(db).summary(user.id)


@router.post("/items", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    data: MemoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MemoryService(db).create_item(user.id, data)


@router.get("/items/{item_id}", response_model=MemoryResponse)
async def get_memory(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MemoryService(db).get_item(user.id, item_id)


@router.patch("/items/{item_id}", response_model=MemoryResponse)
async def update_memory(
    item_id: str,
    data: MemoryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await MemoryService(db).update_item(user.id, item_id, data)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await MemoryService(db).delete_item(user.id, item_id)
