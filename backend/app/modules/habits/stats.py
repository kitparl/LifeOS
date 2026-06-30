from datetime import UTC, date, datetime, timedelta

from app.modules.habits.models import Habit


def _today() -> date:
    return datetime.now(UTC).date()


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _month_start(d: date) -> date:
    return d.replace(day=1)


def is_completed_for_period(habit: Habit, ref: date | None = None) -> bool:
    ref = ref or _today()
    log_dates = {log.log_date for log in habit.logs}
    if habit.frequency == "daily":
        return ref in log_dates
    if habit.frequency == "weekly":
        ws = _week_start(ref)
        return any(_week_start(ld) == ws for ld in log_dates)
    ms = _month_start(ref)
    return any(_month_start(ld) == ms for ld in log_dates)


def calculate_streak(habit: Habit) -> int:
    if not habit.logs:
        return 0
    today = _today()
    streak = 0

    if habit.frequency == "daily":
        cursor = today
        log_dates = {log.log_date for log in habit.logs}
        while cursor in log_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    if habit.frequency == "weekly":
        cursor = _week_start(today)
        weeks = {_week_start(log.log_date) for log in habit.logs}
        while cursor in weeks:
            streak += 1
            cursor -= timedelta(days=7)
        return streak

    cursor = _month_start(today)
    months = {_month_start(log.log_date) for log in habit.logs}
    while cursor in months:
        streak += 1
        if cursor.month == 1:
            cursor = cursor.replace(year=cursor.year - 1, month=12)
        else:
            cursor = cursor.replace(month=cursor.month - 1)
    return streak


def calculate_completion_rate(habit: Habit, lookback_days: int = 30) -> float:
    if not habit.logs:
        return 0.0
    today = _today()
    start = today - timedelta(days=lookback_days - 1)
    log_dates = [log.log_date for log in habit.logs if log.log_date >= start]

    if habit.frequency == "daily":
        expected = lookback_days
        return round(min(len(log_dates) / expected, 1.0) * 100, 1)

    if habit.frequency == "weekly":
        weeks = set()
        d = start
        while d <= today:
            weeks.add(_week_start(d))
            d += timedelta(days=1)
        completed_weeks = {_week_start(ld) for ld in log_dates}
        return round(len(completed_weeks & weeks) / max(len(weeks), 1) * 100, 1)

    months = set()
    d = start
    while d <= today:
        months.add(_month_start(d))
        if d.month == 12:
            d = d.replace(year=d.year + 1, month=1, day=1)
        else:
            d = d.replace(month=d.month + 1, day=1)
    completed_months = {_month_start(ld) for ld in log_dates}
    return round(len(completed_months & months) / max(len(months), 1) * 100, 1)


def count_missed_periods(habit: Habit, lookback_days: int = 30) -> int:
    rate = calculate_completion_rate(habit, lookback_days)
    if habit.frequency == "daily":
        expected = lookback_days
        completed = int(expected * rate / 100)
        return max(expected - completed, 0)
    if habit.frequency == "weekly":
        return max(int((lookback_days / 7)) - int(rate / 100 * (lookback_days / 7)), 0)
    return 0
