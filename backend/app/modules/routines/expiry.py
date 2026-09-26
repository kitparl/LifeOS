from datetime import date

from app.modules.routines.models import Routine


def period_is_outside_today(
    start: date | None,
    end: date | None,
    today: date | None = None,
) -> bool:
    """True when the routine period is in the past / does not contain today.

    - end_date set and end_date < today
    - both start and end set and today not in [start, end]
    Future-only (start > today, no end) stays active.
    """
    today = today or date.today()
    if end is not None and end < today:
        return True
    return start is not None and end is not None and not (start <= today <= end)


def runs_on(routine: Routine, day: date) -> bool:
    """True when the routine is scheduled on ``day`` (weekday, period bounds, and skip dates)."""
    if routine.start_date and day < routine.start_date:
        return False
    if routine.end_date and day > routine.end_date:
        return False
    if day.isoformat() in routine.skip_dates:
        return False
    return day.weekday() in routine.days_of_week
