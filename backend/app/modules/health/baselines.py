"""Pure helpers for health data: merging sources, baselines, trend markers, rolling means, sleep consistency."""

import math
from datetime import date, timedelta
from typing import Literal

Marker = Literal["up", "down", "flat"]
Favourable = Literal["good", "bad"]

FLAT_TOLERANCE = 0.02  # within 2% of the baseline counts as unchanged
CLOCK_ORIGIN_MIN = 18 * 60  # sleep times are measured from 18:00 so times around midnight stay contiguous


def merge_values(
    manual: dict[str, float | int | None] | None, other: dict[str, float | int | None] | None, other_source: str
) -> tuple[dict[str, float | int], dict[str, str]]:
    """Field-by-field merge: a manual value wins, the other source fills the rest.

    Returns (values, sources); keys without a value in either are left out.
    """
    values: dict[str, float | int] = {}
    sources: dict[str, str] = {}
    for key, value in (other or {}).items():
        if value is not None:
            values[key], sources[key] = value, other_source
    for key, value in (manual or {}).items():
        if value is not None:
            values[key], sources[key] = value, "manual"
    return values, sources


def baseline(points: dict[date, float], as_of: date, days: int, min_points: int) -> float | None:
    """Mean of the values on the `days` days before `as_of` (not including it); None with too few values."""
    window = [points[as_of - timedelta(days=i)] for i in range(1, days + 1) if (as_of - timedelta(days=i)) in points]
    return sum(window) / len(window) if len(window) >= min_points else None


def direction(value: float, baseline_value: float, tolerance: float = FLAT_TOLERANCE) -> Marker:
    if baseline_value == 0:
        return "up" if value > 0 else "flat"
    change = (value - baseline_value) / abs(baseline_value)
    if change > tolerance:
        return "up"
    if change < -tolerance:
        return "down"
    return "flat"


def favourable(marker: Marker | None, lower_is_better: bool | None) -> Favourable | None:
    if marker is None or marker == "flat" or lower_is_better is None:
        return None
    moved_down = marker == "down"
    return "good" if moved_down == lower_is_better else "bad"


def rolling_mean(points: dict[date, float], days: list[date], window: int) -> list[float | None]:
    """For each day, the mean of the values in the `window` days ending on it (None when there are none)."""
    out: list[float | None] = []
    for day in days:
        values = [points[day - timedelta(days=i)] for i in range(window) if (day - timedelta(days=i)) in points]
        out.append(sum(values) / len(values) if values else None)
    return out


def clock_spread(minutes: list[int]) -> float | None:
    """Standard deviation in minutes of times of day (minutes after midnight); None with fewer than 3 times."""
    if len(minutes) < 3:
        return None
    shifted = [(m - CLOCK_ORIGIN_MIN) % 1440 for m in minutes]
    mean = sum(shifted) / len(shifted)
    return math.sqrt(sum((m - mean) ** 2 for m in shifted) / len(shifted))
