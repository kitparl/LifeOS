from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.sticky_notes.schemas import (
    StickyNoteCreate,
    StickyNoteMonth,
    StickyNoteResponse,
    StickyNoteUpdate,
)
from app.modules.sticky_notes.service import StickyNoteService

router = APIRouter(prefix="/sticky-notes", tags=["sticky-notes"])


@router.get("/months", response_model=list[StickyNoteMonth])
async def list_sticky_note_months(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).list_months(user.id)


@router.get("/recent", response_model=list[StickyNoteResponse])
async def list_recent_sticky_notes(
    limit: int = Query(default=5, ge=1, le=25),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).list_recent(user.id, limit)


@router.get("/search", response_model=list[StickyNoteResponse])
async def search_sticky_notes(
    q: str = Query(default="", min_length=0, max_length=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).search(user.id, q)


@router.get("/all", response_model=list[StickyNoteResponse])
async def list_all_sticky_notes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).list_all(user.id)


@router.get("/deleted", response_model=list[StickyNoteResponse])
async def list_deleted_sticky_notes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).list_deleted(user.id)


@router.get("", response_model=list[StickyNoteResponse])
async def list_sticky_notes(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).list_by_month(user.id, month)


@router.post("", response_model=StickyNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_sticky_note(
    data: StickyNoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).create_note(user.id, data)


@router.get("/{note_id}", response_model=StickyNoteResponse)
async def get_sticky_note(
    note_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).get_note(user.id, note_id)


@router.patch("/{note_id}", response_model=StickyNoteResponse)
async def update_sticky_note(
    note_id: str,
    data: StickyNoteUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).update_note(user.id, note_id, data)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sticky_note(
    note_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await StickyNoteService(db).delete_note(user.id, note_id)


@router.post("/{note_id}/restore", response_model=StickyNoteResponse)
async def restore_sticky_note(
    note_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await StickyNoteService(db).restore_note(user.id, note_id)
