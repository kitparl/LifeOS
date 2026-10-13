"""Owner endpoints for a trip's share link and plan versions. Signed-in owner only; others get 404."""

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.travel.schemas.shares import (
    ApplyResult,
    EventOut,
    LockRequest,
    LockResult,
    ShareOut,
    ShareSettingsUpdate,
    VersionDetail,
    VersionRename,
    VersionRow,
)
from app.modules.travel.services.share_service import ShareService

router = APIRouter(prefix="/trips/{trip_id}/share")

VersionId = Path(max_length=36, pattern=r"^[A-Za-z0-9-]+$")
ContributorId = Path(max_length=36, pattern=r"^[A-Za-z0-9-]+$")


@router.post("", response_model=ShareOut, status_code=status.HTTP_201_CREATED)
async def create_share(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ShareService(db).create(user, trip_id)


@router.get("", response_model=ShareOut)
async def get_share(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ShareService(db).get(user, trip_id)


@router.patch("/settings", response_model=ShareOut)
async def update_settings(
    trip_id: str,
    data: ShareSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ShareService(db).update_settings(user, trip_id, data)


@router.post("/revoke", response_model=ShareOut)
async def revoke(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ShareService(db).revoke(user, trip_id)


@router.post("/new-link", response_model=ShareOut)
async def new_link(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ShareService(db).new_link(user, trip_id)


@router.post("/lock", response_model=LockResult)
async def lock(
    trip_id: str, data: LockRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await ShareService(db).lock(user, trip_id, data.version_id, data.apply)


@router.post("/unlock", response_model=ShareOut)
async def unlock(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ShareService(db).unlock(user, trip_id)


@router.get("/versions", response_model=list[VersionRow])
async def list_versions(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ShareService(db).list_versions(user, trip_id)


@router.post("/versions", response_model=VersionRow, status_code=status.HTTP_201_CREATED)
async def snapshot_trip(trip_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ShareService(db).snapshot_trip(user, trip_id)


@router.get("/versions/{version_id}", response_model=VersionDetail)
async def get_version(
    trip_id: str,
    version_id: str = VersionId,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ShareService(db).get_version(user, trip_id, version_id)


@router.patch("/versions/{version_id}", response_model=VersionRow)
async def rename_version(
    trip_id: str,
    data: VersionRename,
    version_id: str = VersionId,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ShareService(db).rename_version(user, trip_id, version_id, data.label)


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    trip_id: str,
    version_id: str = VersionId,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await ShareService(db).delete_version(user, trip_id, version_id)


@router.post("/versions/{version_id}/apply", response_model=ApplyResult)
async def apply_version(
    trip_id: str,
    version_id: str = VersionId,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ShareService(db).apply(user, trip_id, version_id)


@router.get("/versions/{version_id}/export", response_class=Response)
async def export_version(
    trip_id: str,
    version_id: str = VersionId,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pdf, name = await ShareService(db).version_pdf(user, trip_id, version_id)
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.delete("/contributors/{contributor_id}", response_model=ShareOut)
async def remove_contributor(
    trip_id: str,
    contributor_id: str = ContributorId,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ShareService(db).remove_contributor(user, trip_id, contributor_id)


@router.get("/events", response_model=list[EventOut])
async def list_events(
    trip_id: str,
    limit: int = Query(default=20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ShareService(db).events(user, trip_id, limit)
