"""AI insight provider interface, placeholder, and the LLM-backed implementation.

LlmInsightProvider resolves the `analytics.insights` use case through the AI gateway and
falls back to PlaceholderInsightProvider when no provider is connected or the call fails.
"""

from __future__ import annotations

import logging
from typing import Literal, Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.adapters.base import AiProviderError, MissingCredentialError, parse_json_object
from app.modules.ai.gateway import AiGateway
from app.modules.ai.use_cases import USE_CASE_ANALYTICS_INSIGHTS
from app.modules.analytics_dashboard.aggregators.overview_aggregator import build_overview
from app.modules.analytics_dashboard.cache import analytics_cache
from app.modules.analytics_dashboard.schemas import AiInsightBlock, AiInsightsResponse

logger = logging.getLogger(__name__)

InsightPeriod = Literal["daily", "weekly", "monthly", "predictions"]
_PERIODS: tuple[tuple[InsightPeriod, str], ...] = (
    ("daily", "Daily Insights"),
    ("weekly", "Weekly Insights"),
    ("monthly", "Monthly Insights"),
    ("predictions", "Predictions"),
)
# Insights cost one LLM call; reuse them across dashboard loads for a while.
INSIGHTS_CACHE_TTL_SECONDS = 600.0
_OVERVIEW_RANGE_DAYS = 30
_CONTEXT_MAX_CHARS = 6000
_MAX_ITEMS_PER_PERIOD = 4
_ITEM_MAX_CHARS = 240


@runtime_checkable
class AnalyticsInsightProvider(Protocol):
    async def get_daily_insights(self, user_id: str) -> AiInsightBlock: ...

    async def get_weekly_insights(self, user_id: str) -> AiInsightBlock: ...

    async def get_monthly_insights(self, user_id: str) -> AiInsightBlock: ...

    async def get_predictions(self, user_id: str) -> AiInsightBlock: ...

    async def get_all(self, user_id: str) -> AiInsightsResponse: ...


_PERIOD_TITLES: dict[InsightPeriod, str] = dict(_PERIODS)
_PLACEHOLDER_MESSAGES: dict[InsightPeriod, str] = {
    "daily": "AI daily insights coming soon",
    "weekly": "AI weekly insights coming soon",
    "monthly": "AI monthly insights coming soon",
    "predictions": "AI predictions coming soon",
}


def _placeholder_block(period: InsightPeriod) -> AiInsightBlock:
    return AiInsightBlock(
        period=period,
        status="coming_soon",
        title=_PERIOD_TITLES[period],
        items=[],
        message=_PLACEHOLDER_MESSAGES[period],
    )


class PlaceholderInsightProvider:
    """Returns Coming Soon blocks (used when no AI provider is connected or the call fails)."""

    async def get_daily_insights(self, user_id: str) -> AiInsightBlock:
        return _placeholder_block("daily")

    async def get_weekly_insights(self, user_id: str) -> AiInsightBlock:
        return _placeholder_block("weekly")

    async def get_monthly_insights(self, user_id: str) -> AiInsightBlock:
        return _placeholder_block("monthly")

    async def get_predictions(self, user_id: str) -> AiInsightBlock:
        return _placeholder_block("predictions")

    async def get_all(self, user_id: str) -> AiInsightsResponse:
        return AiInsightsResponse(**{period: _placeholder_block(period) for period, _ in _PERIODS})


def _items(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    items = [str(x).strip()[:_ITEM_MAX_CHARS] for x in raw if str(x).strip()]
    return items[:_MAX_ITEMS_PER_PERIOD]


class LlmInsightProvider:
    """One LLM call produces all four insight blocks from the analytics overview."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.placeholder = PlaceholderInsightProvider()

    async def get_all(self, user_id: str) -> AiInsightsResponse:
        cache_key = f"{user_id}:ai_insights"
        cached = analytics_cache.get(cache_key)
        if cached is not None:
            return cached

        overview = await build_overview(self.db, user_id, _OVERVIEW_RANGE_DAYS)
        system = (
            "You are a personal productivity analyst. Using ONLY the JSON metrics provided, "
            "write short, specific, encouraging insights. Do not invent numbers. "
            "Respond with ONLY valid JSON (no markdown fences) matching this shape:\n"
            '{"daily": ["..."], "weekly": ["..."], "monthly": ["..."], "predictions": ["..."]}\n'
            f"Give at most {_MAX_ITEMS_PER_PERIOD} items per key, one sentence each."
        )
        context = overview.model_dump_json()[:_CONTEXT_MAX_CHARS]
        try:
            raw = await AiGateway(self.db).chat(
                user_id, USE_CASE_ANALYTICS_INSIGHTS, system, f"Metrics (last {_OVERVIEW_RANGE_DAYS} days):\n{context}"
            )
            data = parse_json_object(raw)
        except MissingCredentialError:
            return await self.placeholder.get_all(user_id)
        except AiProviderError:
            logger.exception("Analytics insights provider failed")
            return await self.placeholder.get_all(user_id)

        blocks: dict[str, AiInsightBlock] = {}
        for period, title in _PERIODS:
            items = _items(data.get(period))
            blocks[period] = AiInsightBlock(
                period=period,
                status="ready",
                title=title,
                items=items,
                message="" if items else "No insight for this period yet.",
            )
        result = AiInsightsResponse(**blocks)
        analytics_cache.set(cache_key, result, ttl=INSIGHTS_CACHE_TTL_SECONDS)
        return result

    async def get_daily_insights(self, user_id: str) -> AiInsightBlock:
        return (await self.get_all(user_id)).daily

    async def get_weekly_insights(self, user_id: str) -> AiInsightBlock:
        return (await self.get_all(user_id)).weekly

    async def get_monthly_insights(self, user_id: str) -> AiInsightBlock:
        return (await self.get_all(user_id)).monthly

    async def get_predictions(self, user_id: str) -> AiInsightBlock:
        return (await self.get_all(user_id)).predictions
