"""Pure mapping between Google Calendar events and LifeOS calendar fields."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MAX_TITLE = 200
MAX_LOCATION = 200
MAX_SOURCE_ID = 255


@dataclass(frozen=True)
class MappedEvent:
    source_id: str
    title: str
    description: str | None
    location: str | None
    starts_at: datetime
    ends_at: datetime | None
    all_day: bool


def _zone(tz_name: str | None) -> timezone | ZoneInfo:
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return timezone.utc


def _parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _truncate(value: object, limit: int) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()[:limit]


def map_google_event(item: dict, calendar_tz: str | None) -> MappedEvent | None:
    """Map one Google event to LifeOS fields. Returns None for events we skip.

    All-day events: Google gives ``date`` with an exclusive end; LifeOS stores
    local midnight .. 23:59:59 of the last day (same as the Calendar UI creates).
    """
    event_id = item.get("id")
    if not isinstance(event_id, str) or not event_id or len(event_id) > MAX_SOURCE_ID:
        return None
    if item.get("status") == "cancelled":
        return None
    start = item.get("start") if isinstance(item.get("start"), dict) else {}
    end = item.get("end") if isinstance(item.get("end"), dict) else {}

    try:
        if start.get("dateTime"):
            starts_at = _parse_dt(str(start["dateTime"]))
            ends_at = _parse_dt(str(end["dateTime"])) if end.get("dateTime") else None
            all_day = False
        elif start.get("date"):
            tz = _zone(start.get("timeZone") or calendar_tz)
            start_day = date.fromisoformat(str(start["date"]))
            end_day = date.fromisoformat(str(end["date"])) - timedelta(days=1) if end.get("date") else start_day
            end_day = max(end_day, start_day)
            starts_at = datetime.combine(start_day, time(0, 0), tzinfo=tz).astimezone(timezone.utc)
            ends_at = datetime.combine(end_day, time(23, 59, 59), tzinfo=tz).astimezone(timezone.utc)
            all_day = True
        else:
            return None
    except (ValueError, TypeError):
        return None

    return MappedEvent(
        source_id=event_id,
        title=_truncate(item.get("summary"), MAX_TITLE) or "(No title)",
        description=item.get("description") if isinstance(item.get("description"), str) else None,
        location=_truncate(item.get("location"), MAX_LOCATION),
        starts_at=starts_at,
        ends_at=ends_at,
        all_day=all_day,
    )


def to_google_patch(
    *,
    title: str,
    description: str | None,
    location: str | None,
    starts_at: datetime,
    ends_at: datetime | None,
    all_day: bool,
    calendar_tz: str | None = None,
) -> dict:
    """Build a PATCH body for a LifeOS edit of a Google-linked event (two-way only)."""
    if starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=timezone.utc)
    if ends_at is not None and ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=timezone.utc)
    body: dict = {"summary": title, "description": description or "", "location": location or ""}
    if all_day:
        tz = _zone(calendar_tz)
        first = starts_at.astimezone(tz).date()
        last = (ends_at or starts_at).astimezone(tz).date()
        last = max(last, first)
        body["start"] = {"date": first.isoformat(), "dateTime": None}
        body["end"] = {"date": (last + timedelta(days=1)).isoformat(), "dateTime": None}
    else:
        end = ends_at or starts_at + timedelta(hours=1)
        body["start"] = {"dateTime": starts_at.isoformat(), "date": None}
        body["end"] = {"dateTime": end.isoformat(), "date": None}
    return body
