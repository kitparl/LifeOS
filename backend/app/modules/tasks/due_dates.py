"""Due-date tokens shared by the AI quick-add and the Telegram task flows."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

_NOON = time(12, 0)


def noon_utc(day: date) -> datetime:
    """Tasks created from a bare date are due at 12:00 UTC so the day survives timezone shifts."""
    return datetime.combine(day, _NOON, tzinfo=timezone.utc)


def resolve_due_token(token: str, today: date) -> date | None:
    """Resolve ``today`` / ``tomorrow`` / ``YYYY-MM-DD`` (lowercase token); None when unrecognised."""
    if token == "today":
        return today
    if token == "tomorrow":
        return today + timedelta(days=1)
    try:
        return date.fromisoformat(token)
    except ValueError:
        return None
