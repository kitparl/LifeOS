"""Future AI engine interfaces — placeholders only. No implementation.

Each engine should be implemented later without changing the Analytics Dashboard
service orchestration beyond swapping the provider.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class InsightEngine(Protocol):
    """TODO: Generate natural-language insights from aggregated analytics payloads."""

    async def generate(self, user_id: str, payload: dict[str, Any]) -> list[str]: ...


@runtime_checkable
class PredictionEngine(Protocol):
    """TODO: Forecast goal completion, burnout risk, and habit adherence."""

    async def predict(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...


@runtime_checkable
class RecommendationEngine(Protocol):
    """TODO: Recommend next actions based on analytics patterns."""

    async def recommend(self, user_id: str, payload: dict[str, Any]) -> list[str]: ...


@runtime_checkable
class TrendAnalyzer(Protocol):
    """TODO: Detect upward/downward trends across modules."""

    async def analyze(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...


@runtime_checkable
class PatternDetector(Protocol):
    """TODO: Detect recurring behavioral patterns (time-of-day, weekday, etc.)."""

    async def detect(self, user_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]: ...
