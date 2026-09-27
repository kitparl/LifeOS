from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.pagination import Pagination, pagination_params
from app.modules.auth.models import User
from app.modules.travel.schemas.routes import RouteOut, RouteRequest
from app.modules.travel.schemas.trips import (
    DayCreate,
    DayUpdate,
    ItemCreate,
    ItemUpdate,
    ItineraryOrder,
    TripCreate,
    TripDetail,
    TripListItem,
    TripPlaceAdd,
    TripStatus,
    TripStatusChange,
    TripUpdate,
)
from app.modules.travel.services.route_service import RouteService
from app.modules.travel.services.trip_service import TripService

router = APIRouter(prefix="/trips")


@router.get("", response_model=list[TripListItem])
async def list_trips(
    response: Response,
    status_filter: TripStatus | None = Query(default=None, alias="status"),
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await TripService(db).list_trips(user.id, status_filter, pagination)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("", response_model=TripDetail, status_code=status.HTTP_201_CREATED)
async def create_trip(data: TripCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await TripService(db).create(user.id, data)


@router.get("/{trip_id}", response_model=TripDetail)
async def get_trip(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await TripService(db).detail(user.id, trip_id)


@router.patch("/{trip_id}", response_model=TripDetail)
async def update_trip(
    trip_id: str, data: TripUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await TripService(db).update(user.id, trip_id, data)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await TripService(db).delete(user.id, trip_id)


@router.post("/{trip_id}/confirm", response_model=TripDetail)
async def confirm_trip(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await TripService(db).confirm(user.id, trip_id)


@router.post("/{trip_id}/draft", response_model=TripDetail)
async def trip_back_to_draft(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await TripService(db).back_to_draft(user.id, trip_id)


@router.post("/{trip_id}/status", response_model=TripDetail)
async def set_trip_status(
    trip_id: str, data: TripStatusChange, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await TripService(db).set_status(user.id, trip_id, data.status)


@router.post("/{trip_id}/complete", response_model=TripDetail)
async def complete_trip(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await TripService(db).complete(user.id, trip_id)


@router.post("/{trip_id}/places/{place_id}", response_model=TripDetail)
async def add_trip_place(
    trip_id: str,
    place_id: str,
    data: TripPlaceAdd | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TripService(db).add_place(user.id, trip_id, place_id, data.day_id if data else None)


@router.delete("/{trip_id}/places/{place_id}", response_model=TripDetail)
async def remove_trip_place(
    trip_id: str, place_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await TripService(db).remove_place(user.id, trip_id, place_id)


@router.post("/{trip_id}/days", response_model=TripDetail, status_code=status.HTTP_201_CREATED)
async def add_trip_day(
    trip_id: str, data: DayCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await TripService(db).add_day(user.id, trip_id, data)


@router.post("/{trip_id}/days/fill", response_model=TripDetail)
async def fill_trip_days(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await TripService(db).fill_days(user.id, trip_id)


@router.patch("/{trip_id}/days/{day_id}", response_model=TripDetail)
async def update_trip_day(
    trip_id: str,
    day_id: str,
    data: DayUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TripService(db).update_day(user.id, trip_id, day_id, data)


@router.delete("/{trip_id}/days/{day_id}", response_model=TripDetail)
async def delete_trip_day(
    trip_id: str, day_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await TripService(db).delete_day(user.id, trip_id, day_id)


@router.post("/{trip_id}/items", response_model=TripDetail, status_code=status.HTTP_201_CREATED)
async def add_trip_item(
    trip_id: str, data: ItemCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await TripService(db).add_item(user.id, trip_id, data)


@router.patch("/{trip_id}/items/{item_id}", response_model=TripDetail)
async def update_trip_item(
    trip_id: str,
    item_id: str,
    data: ItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await TripService(db).update_item(user.id, trip_id, item_id, data)


@router.delete("/{trip_id}/items/{item_id}", response_model=TripDetail)
async def delete_trip_item(
    trip_id: str, item_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await TripService(db).delete_item(user.id, trip_id, item_id)


@router.put("/{trip_id}/itinerary/order", response_model=TripDetail)
async def reorder_itinerary(
    trip_id: str, data: ItineraryOrder, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await TripService(db).reorder(user.id, trip_id, data)


@router.post("/{trip_id}/route", response_model=RouteOut)
async def compute_trip_route(
    trip_id: str, data: RouteRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await RouteService(db).compute_trip_route(user.id, trip_id, data.mode)
