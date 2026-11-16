from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import async_session_factory, get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.integrations.garmin.import_service import GarminImportService, stage_uploads, to_response
from app.modules.integrations.garmin.schemas import (
    DeleteImportedResult,
    ImportedSummary,
    ImportJobResponse,
    ImportRange,
)

router = APIRouter(prefix="/integrations/garmin", tags=["garmin"])


def get_session_factory() -> async_sessionmaker:
    """The factory the background import opens its own sessions from (overridden in tests)."""
    return async_session_factory


@router.post("/imports", response_model=ImportJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_import(
    files: list[UploadFile] = File(...),
    range_mode: ImportRange = Form(default="12m", alias="range"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    factory: async_sessionmaker = Depends(get_session_factory),
):
    service = GarminImportService(db)
    staged = await stage_uploads(files)
    job = await service.start(user.id, staged, range_mode, factory)
    return to_response(job)


@router.get("/imports", response_model=list[ImportJobResponse])
async def list_imports(
    response: Response,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await GarminImportService(db).list_jobs(user.id, limit, offset)
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/imports/{job_id}", response_model=ImportJobResponse)
async def get_import(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GarminImportService(db).get_job(user.id, job_id)


@router.get("/data/summary", response_model=ImportedSummary)
async def imported_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GarminImportService(db).summary(user.id)


@router.delete("/data", response_model=DeleteImportedResult)
async def delete_imported_data(
    include_health: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await GarminImportService(db).delete_imported_data(user.id, include_health)
