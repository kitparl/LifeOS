from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import PayloadTooLargeError
from app.core.pagination import Pagination, pagination_params
from app.modules.auth.models import User
from app.modules.travel.gpx import MAX_GPX_BYTES
from app.modules.travel.schemas.adventures import (
    AdventureCreate,
    AdventureDetail,
    AdventureOut,
    AdventureUpdate,
    GpxPreview,
    WaypointsUpdate,
)
from app.modules.travel.schemas.routes import RouteDetail
from app.modules.travel.services.adventure_service import AdventureService
from app.modules.travel.services.gpx_service import GpxService
from app.modules.travel.services.route_service import RouteService

router = APIRouter()

_ID = r"^[A-Za-z0-9-]{1,36}$"


async def _read_gpx(file: UploadFile) -> bytes:
    """Read at most MAX_GPX_BYTES + 1 so an oversized upload is rejected without buffering it all."""
    data = await file.read(MAX_GPX_BYTES + 1)
    if len(data) > MAX_GPX_BYTES:
        raise PayloadTooLargeError("GPX file is larger than 10 MB")
    return data


@router.get("/adventures", response_model=list[AdventureOut])
async def list_adventures(
    response: Response,
    trip_id: str | None = Query(default=None, pattern=_ID),
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await AdventureService(db).list_adventures(user.id, trip_id, pagination)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/adventures", response_model=AdventureDetail, status_code=status.HTTP_201_CREATED)
async def create_adventure(
    data: AdventureCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await AdventureService(db).create(user.id, data)


@router.get("/adventures/{adventure_id}", response_model=AdventureDetail)
async def get_adventure(adventure_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await AdventureService(db).detail(user.id, adventure_id)


@router.patch("/adventures/{adventure_id}", response_model=AdventureDetail)
async def update_adventure(
    adventure_id: str, data: AdventureUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await AdventureService(db).update(user.id, adventure_id, data)


@router.delete("/adventures/{adventure_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_adventure(
    adventure_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await AdventureService(db).delete(user.id, adventure_id)


@router.put("/adventures/{adventure_id}/waypoints", response_model=AdventureDetail)
async def set_adventure_waypoints(
    adventure_id: str, data: WaypointsUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await AdventureService(db).set_waypoints(user.id, adventure_id, data)


@router.post("/gpx/preview", response_model=GpxPreview)
async def preview_gpx(
    file: UploadFile = File(...), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return GpxService(db).preview(await _read_gpx(file))


@router.post("/gpx", response_model=RouteDetail, status_code=status.HTTP_201_CREATED)
async def import_gpx(
    file: UploadFile = File(...),
    name: str = Form(min_length=1, max_length=200),
    trip_id: str | None = Form(default=None, pattern=_ID),
    adventure_id: str | None = Form(default=None, pattern=_ID),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GpxService(db).save(user.id, await _read_gpx(file), name.strip(), trip_id, adventure_id)


@router.get("/routes/{route_id}/gpx")
async def export_gpx(route_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    filename, body = await GpxService(db).export(user.id, route_id)
    return Response(
        content=body,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/routes/{route_id}/elevation", response_model=RouteDetail)
async def route_elevation(route_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await RouteService(db).fill_elevation(user.id, route_id)
