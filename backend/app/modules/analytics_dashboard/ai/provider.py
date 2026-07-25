"""AI insight provider interfaces and placeholder implementation.

Future AI implementations should only replace PlaceholderInsightProvider.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.modules.analytics_dashboard.schemas import AiInsightBlock, AiInsightsResponse


@runtime_checkable
class AnalyticsInsightProvider(Protocol):
    async def get_daily_insights(self, user_id: str) -> AiInsightBlock: ...

    async def get_weekly_insights(self, user_id: str) -> AiInsightBlock: ...

    async def get_monthly_insights(self, user_id: str) -> AiInsightBlock: ...

    async def get_predictions(self, user_id: str) -> AiInsightBlock: ...


class PlaceholderInsightProvider:
    """Returns Coming Soon blocks. Swap this class for a real LLM-backed provider later."""

    async def get_daily_insights(self, user_id: str) -> AiInsightBlock:
        return AiInsightBlock(
            period="daily",
            status="coming_soon",
            title="Daily Insights",
            items=[],
            message="AI daily insights coming soon",
        )

    async def get_weekly_insights(self, user_id: str) -> AiInsightBlock:
        return AiInsightBlock(
            period="weekly",
            status="coming_soon",
            title="Weekly Insights",
            items=[],
            message="AI weekly insights coming soon",
        )

    async def get_monthly_insights(self, user_id: str) -> AiInsightBlock:
        return AiInsightBlock(
            period="monthly",
            status="coming_soon",
            title="Monthly Insights",
            items=[],
            message="AI monthly insights coming soon",
        )

    async def get_predictions(self, user_id: str) -> AiInsightBlock:
        return AiInsightBlock(
            period="predictions",
            status="coming_soon",
            title="Predictions",
            items=[],
            message="AI predictions coming soon",
        )

    async def get_all(self, user_id: str) -> AiInsightsResponse:
        return AiInsightsResponse(
            daily=await self.get_daily_insights(user_id),
            weekly=await self.get_weekly_insights(user_id),
            monthly=await self.get_monthly_insights(user_id),
            predictions=await self.get_predictions(user_id),
        )
