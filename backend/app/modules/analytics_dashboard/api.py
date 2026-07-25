"""Analytics Dashboard API — read-only aggregation endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.analytics_dashboard.schemas import (
    AiInsightsResponse,
    AnalyticsOverview,
    GoalAnalytics,
    HabitAnalytics,
    JournalAnalytics,
    ProductivityAnalytics,
    WidgetDescriptor,
)
from app.modules.analytics_dashboard.service import AnalyticsDashboardService
from app.modules.auth.models import User

router = APIRouter(prefix="/analytics/dashboard", tags=["analytics-dashboard"])


@router.get("", response_model=AnalyticsOverview)
async def analytics_overview(
    range_days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverview:
    return await AnalyticsDashboardService(db).overview(user.id, range_days)


@router.get("/summary", response_model=AnalyticsOverview)
async def analytics_dashboard_summary(
    range_days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverview:
    return await AnalyticsDashboardService(db).summary(user.id, range_days)


@router.get("/productivity", response_model=ProductivityAnalytics)
async def analytics_productivity(
    range_days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProductivityAnalytics:
    return await AnalyticsDashboardService(db).productivity(user.id, range_days)


@router.get("/goals", response_model=GoalAnalytics)
async def analytics_goals(
    range_days: int = Query(90, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GoalAnalytics:
    return await AnalyticsDashboardService(db).goals(user.id, range_days)


@router.get("/habits", response_model=HabitAnalytics)
async def analytics_habits(
    range_days: int = Query(90, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HabitAnalytics:
    return await AnalyticsDashboardService(db).habits(user.id, range_days)


@router.get("/journal", response_model=JournalAnalytics)
async def analytics_journal(
    range_days: int = Query(90, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JournalAnalytics:
    return await AnalyticsDashboardService(db).journal(user.id, range_days)


@router.get("/ai", response_model=AiInsightsResponse)
async def analytics_ai(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AiInsightsResponse:
    return await AnalyticsDashboardService(db).ai_insights(user.id)


@router.get("/widgets", response_model=list[WidgetDescriptor])
async def analytics_widgets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WidgetDescriptor]:
    return AnalyticsDashboardService(db).widgets()
