"""Server-side proxy for Google Maps lookups; the browser never talks to Google (requirements D-02)."""

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.travel.schemas.places import GeoLookupOut, ReverseGeocodeIn, SuggestionsOut
from app.modules.travel.schemas.usage import MapsStatus
from app.modules.travel.services.lookup_service import LookupService

router = APIRouter(prefix="/maps")

_SESSION = r"^[A-Za-z0-9-]{8,64}$"


@router.get("/status", response_model=MapsStatus)
async def maps_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await LookupService(db).status(user.id)


@router.post("/reverse-geocode", response_model=GeoLookupOut)
async def reverse_geocode(
    data: ReverseGeocodeIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await LookupService(db).reverse_geocode(user.id, data.lat, data.lng)


@router.get("/autocomplete", response_model=SuggestionsOut)
async def autocomplete(
    q: str = Query(min_length=1, max_length=100),
    session: str = Query(pattern=_SESSION),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bias = (lat, lng) if lat is not None and lng is not None else None
    return await LookupService(db).autocomplete(user.id, q, session, bias)


@router.get("/place/{external_place_id}", response_model=GeoLookupOut)
async def place_details(
    external_place_id: str = Path(max_length=255, pattern=r"^[A-Za-z0-9_\-:.]+$"),
    session: str | None = Query(default=None, pattern=_SESSION),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LookupService(db).place_details(user.id, external_place_id, session)
