"""Pure date/schedule arithmetic for recurring expenses and loan EMI schedules.

Everything here is deliberately free of the database and of `today` lookups —
callers pass the reference date in. That keeps the tricky parts (month-end
clamping, end-date boundaries, tenure walking) directly testable.
"""

from __future__ import annotations

import calendar
from datetime import date

MONTHLY = "monthly"

PERIOD_PRESETS = ("this_month", "last_month", "this_year", "custom")


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def clamp_day(year: int, month: int, day: int) -> date:
    """Build a date, pulling `day` back to the last valid day of the month.

    Day 31 in February becomes the 28th (29th in a leap year), which is what a
    "every month on the 31st" commitment means in practice.
    """
    return date(year, month, min(max(day, 1), days_in_month(year, month)))


def add_months(year: int, month: int, count: int) -> tuple[int, int]:
    index = (year * 12 + (month - 1)) + count
    return index // 12, index % 12 + 1


def period_key(value: date) -> str:
    """The `YYYY-MM` slot key a generated row occupies."""
    return f"{value.year:04d}-{value.month:02d}"


def month_sequence(start: date, through: date) -> list[tuple[int, int]]:
    """Every (year, month) from `start`'s month to `through`'s month, inclusive."""
    if through < start:
        return []
    months: list[tuple[int, int]] = []
    year, month = start.year, start.month
    while (year, month) <= (through.year, through.month):
        months.append((year, month))
        year, month = add_months(year, month, 1)
    return months


def recurring_due_dates(
    start_date: date,
    end_date: date | None,
    day_of_month: int,
    through: date,
) -> list[date]:
    """Due dates for a monthly definition, from `start_date` up to `through`.

    A month is skipped when its clamped due date falls before the definition's
    start date (so a definition starting on the 20th does not back-fill the 5th
    of that same month) or after its end date.
    """
    limit = through if end_date is None else min(through, end_date)
    due_dates: list[date] = []
    for year, month in month_sequence(start_date, limit):
        due = clamp_day(year, month, day_of_month)
        if due < start_date or due > limit:
            continue
        due_dates.append(due)
    return due_dates


def emi_schedule(
    emi_start_date: date,
    emi_day: int,
    tenure_months: int,
    amount: float,
) -> list[tuple[int, date, float]]:
    """The full `(emi_number, due_date, amount)` schedule for a loan.

    EMI #1 falls on `emi_day` of the EMI start month; if that day has already
    passed within the start month, it rolls to the following month so no EMI is
    ever scheduled before the loan's EMI start date.
    """
    if tenure_months < 1:
        return []

    year, month = emi_start_date.year, emi_start_date.month
    if clamp_day(year, month, emi_day) < emi_start_date:
        year, month = add_months(year, month, 1)

    schedule: list[tuple[int, date, float]] = []
    for offset in range(tenure_months):
        emi_year, emi_month = add_months(year, month, offset)
        schedule.append((offset + 1, clamp_day(emi_year, emi_month, emi_day), amount))
    return schedule


def month_bounds(value: date) -> tuple[date, date]:
    return value.replace(day=1), clamp_day(value.year, value.month, 31)


def period_bounds(
    preset: str,
    today: date,
    start: date | None = None,
    end: date | None = None,
) -> tuple[date, date]:
    """Resolve a filter preset into an inclusive [start, end] range.

    Defaults to the current calendar month — and stays there even when that
    month has no activity.
    """
    if preset == "last_month":
        year, month = add_months(today.year, today.month, -1)
        return month_bounds(date(year, month, 1))
    if preset == "this_year":
        return date(today.year, 1, 1), date(today.year, 12, 31)
    if preset == "custom":
        resolved_start = start or today.replace(day=1)
        resolved_end = end or clamp_day(today.year, today.month, 31)
        if resolved_end < resolved_start:
            resolved_start, resolved_end = resolved_end, resolved_start
        return resolved_start, resolved_end
    return month_bounds(today)
