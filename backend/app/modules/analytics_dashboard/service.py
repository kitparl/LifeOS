"""Analytics Dashboard service — orchestrates aggregators + cache + AI provider."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics_dashboard.aggregators import clamp_range_days
from app.modules.analytics_dashboard.aggregators.focus_aggregator import planned_focus_hours
from app.modules.analytics_dashboard.aggregators.goals_aggregator import build_goal_analytics
from app.modules.analytics_dashboard.aggregators.habits_aggregator import build_habit_analytics
from app.modules.analytics_dashboard.aggregators.journal_aggregator import build_journal_analytics
from app.modules.analytics_dashboard.aggregators.overview_aggregator import build_overview
from app.modules.analytics_dashboard.aggregators.tasks_aggregator import (
    category_distribution,
    completed_series,
    overdue_count,
    task_completion_breakdown,
)
from app.modules.analytics_dashboard.ai.provider import PlaceholderInsightProvider
from app.modules.analytics_dashboard.cache import analytics_cache
from app.modules.analytics_dashboard.schemas import (
    AiInsightsResponse,
    AnalyticsOverview,
    GoalAnalytics,
    HabitAnalytics,
    JournalAnalytics,
    ProductivityAnalytics,
    WidgetDescriptor,
)
from app.modules.analytics_dashboard.widgets import list_widgets


class AnalyticsDashboardService:
    def __init__(
        self,
        db: AsyncSession,
        insight_provider: PlaceholderInsightProvider | None = None,
    ) -> None:
        self.db = db
        self.insights = insight_provider or PlaceholderInsightProvider()

    def _cache_key(self, user_id: str, endpoint: str, range_days: int) -> str:
        return f"{user_id}:{endpoint}:{range_days}"

    async def overview(self, user_id: str, range_days: int = 30) -> AnalyticsOverview:
        range_days = clamp_range_days(range_days, default=30)
        key = self._cache_key(user_id, "overview", range_days)
        cached = analytics_cache.get(key)
        if cached is not None:
            return cached
        data = await build_overview(self.db, user_id, range_days)
        analytics_cache.set(key, data)
        return data

    async def summary(self, user_id: str, range_days: int = 30) -> AnalyticsOverview:
        return await self.overview(user_id, range_days)

    async def productivity(self, user_id: str, range_days: int = 30) -> ProductivityAnalytics:
        range_days = clamp_range_days(range_days, default=30)
        key = self._cache_key(user_id, "productivity", range_days)
        cached = analytics_cache.get(key)
        if cached is not None:
            return cached

        daily, weekly, monthly, heatmap = await completed_series(self.db, user_id, range_days)
        focus, deep = await planned_focus_hours(self.db, user_id, range_days)
        data = ProductivityAnalytics(
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
        analytics_cache.set(key, data)
        return data

    async def goals(self, user_id: str, range_days: int = 90) -> GoalAnalytics:
        range_days = clamp_range_days(range_days, default=90)
        key = self._cache_key(user_id, "goals", range_days)
        cached = analytics_cache.get(key)
        if cached is not None:
            return cached
        data = await build_goal_analytics(self.db, user_id, range_days)
        analytics_cache.set(key, data)
        return data

    async def habits(self, user_id: str, range_days: int = 90) -> HabitAnalytics:
        range_days = clamp_range_days(range_days, default=90)
        key = self._cache_key(user_id, "habits", range_days)
        cached = analytics_cache.get(key)
        if cached is not None:
            return cached
        data = await build_habit_analytics(self.db, user_id, range_days)
        analytics_cache.set(key, data)
        return data

    async def journal(self, user_id: str, range_days: int = 90) -> JournalAnalytics:
        range_days = clamp_range_days(range_days, default=90)
        key = self._cache_key(user_id, "journal", range_days)
        cached = analytics_cache.get(key)
        if cached is not None:
            return cached
        data = await build_journal_analytics(self.db, user_id, range_days)
        analytics_cache.set(key, data)
        return data

    async def ai_insights(self, user_id: str) -> AiInsightsResponse:
        return await self.insights.get_all(user_id)

    def widgets(self) -> list[WidgetDescriptor]:
        return list_widgets()
