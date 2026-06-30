from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.export.service import EXPORT_MODULES, ExportService

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/modules")
async def list_export_modules(user: User = Depends(get_current_user)):
    return {"modules": list(EXPORT_MODULES), "formats": ["json", "csv"]}


@router.get("/{module}")
async def export_module(
    module: str,
    format: str = Query(default="json", alias="format"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ExportService(db).export(user.id, module, format)
