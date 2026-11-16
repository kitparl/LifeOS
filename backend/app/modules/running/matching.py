"""Pure rules for turning a synced activity into a run: local run date and manual-run matching."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# A manual run matches an activity when their distances differ by at most this fraction.
MATCH_DISTANCE_TOLERANCE = 0.03


@dataclass(frozen=True)
class MatchCandidate:
    run_id: str
    distance_km: float
    created_at: datetime


def local_run_date(start_time_utc: datetime, timezone_name: str | None) -> date:
    """Calendar date of the start in the activity's timezone; UTC date when the zone is unknown."""
    start = start_time_utc if start_time_utc.tzinfo else start_time_utc.replace(tzinfo=timezone.utc)
    if timezone_name:
        try:
            return start.astimezone(ZoneInfo(timezone_name)).date()
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return start.astimezone(timezone.utc).date()


def find_match(activity_km: float, candidates: list[MatchCandidate]) -> str | None:
    """Id of the manual run that best matches the activity distance, or None.

    Candidates must already be the user's unlinked manual runs on the activity's run date.
    Closest distance wins; ties go to the earliest created.
    """
    if activity_km <= 0:
        return None
    within = [c for c in candidates if abs(c.distance_km - activity_km) / activity_km <= MATCH_DISTANCE_TOLERANCE]
    if not within:
        return None
    best = min(within, key=lambda c: (abs(c.distance_km - activity_km), c.created_at))
    return best.run_id
