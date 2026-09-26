"""Shared time helpers: UTC "now"/"today" and Asia/Kolkata (IST) boundaries.

Use these instead of calling ``datetime.now(...)`` or ``ZoneInfo(...)`` inline, so every
module agrees on how "now", "today" and naive database timestamps are interpreted.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


def utc_now() -> datetime:
    """Timezone-aware current UTC time (also used as the ORM default for timestamps)."""
    return datetime.now(UTC)


def utc_today() -> date:
    return utc_now().date()


def start_of_day_utc(day: date) -> datetime:
    """00:00 UTC on ``day``."""
    return datetime.combine(day, time.min, tzinfo=UTC)


def as_utc(value: datetime) -> datetime:
    """Treat a naive datetime as UTC (SQLite returns naive values; every stored timestamp is UTC)."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def ist_now() -> datetime:
    return datetime.now(IST)


def ist_today() -> date:
    return ist_now().date()


def safe_zone(name: str | None, default: ZoneInfo = IST) -> ZoneInfo:
    """ZoneInfo for a user-supplied zone name, falling back to ``default`` when blank or unknown."""
    if not name:
        return default
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        logger.warning("Unknown timezone %s — falling back to %s", name, default.key)
        return default
