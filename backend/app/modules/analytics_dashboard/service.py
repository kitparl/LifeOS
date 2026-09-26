"""Analytics Dashboard service — orchestrates aggregators + cache + AI provider."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics_dashboard.aggregators import clamp_range_days
from app.modules.analytics_dashboard.aggregators.focus_aggregator import planned_focus_hours
from app.modules.analytics_dashboard.aggregators.habits_aggregator import build_habit_analytics
from app.modules.analytics_dashboard.aggregators.journal_aggregator import build_journal_analytics
from app.modules.analytics_dashboard.aggregators.overview_aggregator import build_overview
from app.modules.analytics_dashboard.aggregators.tasks_aggregator import (
    category_distribution,
    completed_series,
    overdue_count,
    task_completion_breakdown,
)
from app.modules.analytics_dashboard.ai.provider import AnalyticsInsightProvider, LlmInsightProvider
from app.modules.analytics_dashboard.cache import analytics_cache
from app.modules.analytics_dashboard.schemas import (
    AiInsightsResponse,
    AnalyticsOverview,
    HabitAnalytics,
    JournalAnalytics,
    ProductivityAnalytics,
    WidgetDescriptor,
)
from app.modules.analytics_dashboard.widgets import list_widgets

T = TypeVar("T")


class AnalyticsDashboardService:
    def __init__(
        self,
        db: AsyncSession,
        insight_provider: AnalyticsInsightProvider | None = None,
    ) -> None:
        self.db = db
        self.insights = insight_provider or LlmInsightProvider(db)

    async def _cached(
        self, user_id: str, endpoint: str, range_days: int, build: Callable[[], Awaitable[T]]
    ) -> T:
        """Serve ``build()`` from the short-lived per-user cache (key: user, endpoint, range)."""
        key = f"{user_id}:{endpoint}:{range_days}"
        cached = analytics_cache.get(key)
        if cached is not None:
            return cached
        data = await build()
        analytics_cache.set(key, data)
        return data

    async def overview(self, user_id: str, range_days: int = 30) -> AnalyticsOverview:
        range_days = clamp_range_days(range_days, default=30)
        return await self._cached(
            user_id, "overview", range_days, lambda: build_overview(self.db, user_id, range_days)
        )

    async def summary(self, user_id: str, range_days: int = 30) -> AnalyticsOverview:
        return await self.overview(user_id, range_days)

    async def productivity(self, user_id: str, range_days: int = 30) -> ProductivityAnalytics:
        range_days = clamp_range_days(range_days, default=30)
        return await self._cached(
            user_id, "productivity", range_days, lambda: self._build_productivity(user_id, range_days)
        )

    async def _build_productivity(self, user_id: str, range_days: int) -> ProductivityAnalytics:
        daily, weekly, monthly, heatmap = await completed_series(self.db, user_id, range_days)
        focus, deep = await planned_focus_hours(self.db, user_id, range_days)
        return ProductivityAnalytics(
            daily_tasks=daily,
            weekly_tasks=weekly,
            monthly_tasks=monthly,
            task_completion=await task_completion_breakdown(self.db, user_id, range_days),
            overdue_tasks=await overdue_count(self.db, user_id),
            focus_hours=focus,
            deep_work_hours=deep,
            focus_label="planned",
            category_distribution=await category_distribution(self.db, user_id, range_days),
            calendar_heatmap=heatmap,
            range_days=range_days,
        )

    async def habits(self, user_id: str, range_days: int = 90) -> HabitAnalytics:
        range_days = clamp_range_days(range_days, default=90)
        return await self._cached(
            user_id, "habits", range_days, lambda: build_habit_analytics(self.db, user_id, range_days)
        )

    async def journal(self, user_id: str, range_days: int = 90) -> JournalAnalytics:
        range_days = clamp_range_days(range_days, default=90)
        return await self._cached(
            user_id, "journal", range_days, lambda: build_journal_analytics(self.db, user_id, range_days)
        )

    async def ai_insights(self, user_id: str) -> AiInsightsResponse:
        return await self.insights.get_all(user_id)

    def widgets(self) -> list[WidgetDescriptor]:
        return list_widgets()
