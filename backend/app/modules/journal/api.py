from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.journal.schemas import JournalCreate, JournalListItem, JournalResponse, JournalUpdate
from app.modules.journal.service import JournalService

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("/entries", response_model=list[JournalListItem])
async def list_entries(
    response: Response,
    entry_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await JournalService(db).list_entries(
        user.id, entry_type=entry_type, search=search, limit=limit, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/entries", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    data: JournalCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await JournalService(db).create_entry(user.id, data)


@router.get("/entries/{entry_id}", response_model=JournalResponse)
async def get_entry(
    entry_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await JournalService(db).get_entry(user.id, entry_id)


@router.patch("/entries/{entry_id}", response_model=JournalResponse)
async def update_entry(
    entry_id: str,
    data: JournalUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await JournalService(db).update_entry(user.id, entry_id, data)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await JournalService(db).delete_entry(user.id, entry_id)
