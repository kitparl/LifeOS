from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.learning.schemas import LearningCreate, LearningListItem, LearningResponse, LearningUpdate
from app.modules.learning.service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/items", response_model=list[LearningListItem])
async def list_learning(
    item_type: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).list_items(user.id, item_type)


@router.post("/items", response_model=LearningResponse, status_code=status.HTTP_201_CREATED)
async def create_learning(
    data: LearningCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).create_item(user.id, data)


@router.get("/items/{item_id}", response_model=LearningResponse)
async def get_learning(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).get_item(user.id, item_id)


@router.patch("/items/{item_id}", response_model=LearningResponse)
async def update_learning(
    item_id: str,
    data: LearningUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).update_item(user.id, item_id, data)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_learning(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await LearningService(db).delete_item(user.id, item_id)
