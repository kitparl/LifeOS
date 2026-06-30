from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.analytics.schemas import AnalyticsCharts, AnalyticsSummary
from app.modules.analytics.service import AnalyticsService
from app.modules.auth.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await AnalyticsService(db).summary(user.id)


@router.get("/charts", response_model=AnalyticsCharts)
async def analytics_charts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await AnalyticsService(db).charts(user.id)
