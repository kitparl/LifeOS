"""Shared helpers for analytics aggregators."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def window_start(range_days: int, ref: date | None = None) -> date:
    ref = ref or utc_today()
    return ref - timedelta(days=max(range_days, 1) - 1)


def clamp_range_days(range_days: int, default: int = 30, max_days: int = 365) -> int:
    try:
        n = int(range_days)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, max_days))


def word_count(*parts: str | None) -> int:
    total = 0
    for part in parts:
        if not part:
            continue
        total += len(str(part).split())
    return total
