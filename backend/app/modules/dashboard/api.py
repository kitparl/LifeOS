from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.dashboard.schemas import DashboardSummaryResponse
from app.modules.dashboard.service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummaryResponse:
    return await DashboardService(db).get_summary(user.id)
