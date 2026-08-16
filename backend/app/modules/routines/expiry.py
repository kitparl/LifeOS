from datetime import date


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
    if start is not None and end is not None and not (start <= today <= end):
        return True
    return False
