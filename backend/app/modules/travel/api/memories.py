from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import UnprocessableError
from app.core.pagination import Pagination, pagination_params
from app.modules.auth.models import User
from app.modules.travel.schemas.memories import (
    JournalCreate,
    JournalOut,
    JournalUpdate,
    PhotoMeta,
    PhotoOut,
    PhotoUpdate,
)
from app.modules.travel.services.memory_service import MemoryService

router = APIRouter()

_ID = r"^[A-Za-z0-9-]{1,36}$"


@router.get("/photos", response_model=list[PhotoOut])
async def list_photos(
    response: Response,
    trip_id: str | None = Query(default=None, pattern=_ID),
    place_id: str | None = Query(default=None, pattern=_ID),
    adventure_id: str | None = Query(default=None, pattern=_ID),
    day_id: str | None = Query(default=None, pattern=_ID),
    journal_entry_id: str | None = Query(default=None, pattern=_ID),
    has_location: bool | None = Query(default=None),
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = {
        "trip_id": trip_id,
        "place_id": place_id,
        "adventure_id": adventure_id,
        "day_id": day_id,
        "journal_entry_id": journal_entry_id,
    }
    items, total = await MemoryService(db).list_photos(user.id, filters, has_location, pagination)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/photos", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    lat: float | None = Form(default=None),
    lng: float | None = Form(default=None),
    location_source: str | None = Form(default=None),
    taken_at: datetime | None = Form(default=None),
    caption: str | None = Form(default=None),
    place_id: str | None = Form(default=None),
    trip_id: str | None = Form(default=None),
    day_id: str | None = Form(default=None),
    adventure_id: str | None = Form(default=None),
    journal_entry_id: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        meta = PhotoMeta(
            lat=lat,
            lng=lng,
            location_source=location_source,
            taken_at=taken_at,
            caption=caption,
            place_id=place_id or None,
            trip_id=trip_id or None,
            day_id=day_id or None,
            adventure_id=adventure_id or None,
            journal_entry_id=journal_entry_id or None,
        )
    except ValidationError as exc:
        raise UnprocessableError(exc.errors(include_url=False, include_context=False)[0]["msg"]) from exc
    return await MemoryService(db).upload_photo(user.id, file, meta)


@router.patch("/photos/{photo_id}", response_model=PhotoOut)
async def update_photo(
    photo_id: str, data: PhotoUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await MemoryService(db).update_photo(user.id, photo_id, data)


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(photo_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await MemoryService(db).delete_photo(user.id, photo_id)


@router.get("/journal", response_model=list[JournalOut])
async def list_journal(
    response: Response,
    trip_id: str | None = Query(default=None, pattern=_ID),
    place_id: str | None = Query(default=None, pattern=_ID),
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await MemoryService(db).list_journal(user.id, trip_id, place_id, pagination)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/journal", response_model=JournalOut, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    data: JournalCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await MemoryService(db).create_entry(user.id, data)


@router.get("/journal/{entry_id}", response_model=JournalOut)
async def get_journal_entry(entry_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await MemoryService(db).get_entry(user.id, entry_id)


@router.patch("/journal/{entry_id}", response_model=JournalOut)
async def update_journal_entry(
    entry_id: str, data: JournalUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await MemoryService(db).update_entry(user.id, entry_id, data)


@router.delete("/journal/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal_entry(
    entry_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await MemoryService(db).delete_entry(user.id, entry_id)
