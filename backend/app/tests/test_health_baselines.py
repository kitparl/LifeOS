"""Metric catalogue, validation and the pure baseline logic (Unit 4: health-backend)."""

from datetime import date, timedelta

import pytest
from app.modules.health import baselines
from app.modules.health.metrics import (
    METRIC_BY_KEY,
    METRICS,
    TODAY_KEYS,
    validate_measurement,
    validate_value,
    validate_values,
)
from app.modules.health.models import HealthDay
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import inspect

DAY = date(2026, 5, 20)

# --- Generators (PBT-07: shaped like real health data) --------------------------------------------

metric_values = st.floats(min_value=1.0, max_value=300.0, allow_nan=False, allow_infinity=False)


@st.composite
def daily_series(draw, max_days: int = 60) -> dict[date, float]:
    offsets = draw(st.lists(st.integers(min_value=1, max_value=max_days), unique=True, max_size=max_days))
    return {DAY - timedelta(days=o): draw(metric_values) for o in offsets}


partial_values = st.dictionaries(st.sampled_from(["resting_hr", "hrv_ms", "steps", "sleep_total_min"]), st.one_of(st.none(), st.integers(1, 100)))


def test_catalogue_matches_the_table_columns_and_is_well_formed():
    columns = {c.key for c in inspect(HealthDay).columns}
    assert {m.key for m in METRICS} <= columns
    assert {m.key for m in METRICS} == columns - {"id", "user_id", "date", "source", "created_at", "updated_at"}
    assert len({m.key for m in METRICS}) == len(METRICS)
    assert all(m.min < m.max for m in METRICS)
    assert len(TODAY_KEYS) == 5


@pytest.mark.parametrize(
    ("key", "value"),
    [("resting_hr", 55), ("hrv_ms", 48.5), ("sleep_score", 0), ("sleep_score", 100), ("bed_time_min", 1439), ("steps", 12000.0)],
)
def test_valid_values_are_accepted(key, value):
    assert validate_value(METRIC_BY_KEY[key], value) == value


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("resting_hr", 400), ("resting_hr", 5), ("sleep_score", 101), ("bed_time_min", 1440), ("steps", -1),
        ("resting_hr", "55"), ("resting_hr", True), ("resting_hr", 55.5), ("hrv_ms", float("nan")),
        ("hrv_ms", float("inf")), ("spo2_avg", 20),
    ],
)
def test_invalid_values_are_rejected(key, value):
    with pytest.raises(ValueError):
        validate_value(METRIC_BY_KEY[key], value)


def test_null_clears_and_unknown_keys_are_rejected():
    assert validate_values({"resting_hr": None, "steps": 100}) == {"resting_hr": None, "steps": 100}
    with pytest.raises(ValueError, match="Unknown health metric"):
        validate_values({"password": 1})


def test_measurement_rules_per_kind():
    assert validate_measurement("weight", {"weight_kg": 72.5}) == {"weight_kg": 72.5}
    assert validate_measurement("body_comp", {"body_fat_pct": 18}) == {"body_fat_pct": 18.0}
    assert validate_measurement("blood_pressure", {"systolic": 118, "diastolic": 76, "pulse": 60})["pulse"] == 60.0
    for kind, values in [
        ("weight", {}), ("weight", {"weight_kg": 5}), ("weight", {"weight_kg": 70, "extra": 1}),
        ("body_comp", {}), ("blood_pressure", {"systolic": 120}), ("blood_pressure", {"systolic": 120, "diastolic": 500}),
        ("heartbeat", {"x": 1}), ("weight", {"weight_kg": True}), ("weight", {"weight_kg": "70"}),
    ]:
        with pytest.raises(ValueError):
            validate_measurement(kind, values)


# --- Merge ----------------------------------------------------------------------------------------


def test_manual_values_win_and_the_other_source_fills_the_rest():
    values, sources = baselines.merge_values(
        {"resting_hr": 50, "steps": None}, {"resting_hr": 60, "steps": 9000, "hrv_ms": 45.0}, "garmin"
    )
    assert values == {"resting_hr": 50, "steps": 9000, "hrv_ms": 45.0}
    assert sources == {"resting_hr": "manual", "steps": "garmin", "hrv_ms": "garmin"}


@given(manual=partial_values, garmin=partial_values)
@settings(max_examples=200)
def test_merge_prefers_manual_and_reports_where_each_value_came_from(manual, garmin):
    values, sources = baselines.merge_values(manual, garmin, "garmin")

    for key in set(manual) | set(garmin):
        if manual.get(key) is not None:
            assert values[key] == manual[key] and sources[key] == "manual"
        elif garmin.get(key) is not None:
            assert values[key] == garmin[key] and sources[key] == "garmin"
        else:
            assert key not in values and key not in sources
    assert set(values) == set(sources)


# --- Baselines ------------------------------------------------------------------------------------


def test_baseline_averages_the_previous_days_and_skips_gaps():
    points = {DAY - timedelta(days=1): 50.0, DAY - timedelta(days=3): 60.0, DAY - timedelta(days=5): 70.0, DAY: 999.0}
    assert baselines.baseline(points, DAY, 7, 3) == 60.0  # today's own value is not part of it
    assert baselines.baseline(points, DAY, 7, 4) is None


@given(points=daily_series(), days=st.sampled_from([7, 30]), min_points=st.integers(1, 8))
@settings(max_examples=200)
def test_baseline_lies_within_the_values_it_averages_and_needs_enough_of_them(points, days, min_points):
    window = [v for d, v in points.items() if 1 <= (DAY - d).days <= days]
    result = baselines.baseline(points, DAY, days, min_points)

    if len(window) < min_points:
        assert result is None
    else:
        assert min(window) - 1e-9 <= result <= max(window) + 1e-9


@pytest.mark.parametrize(
    ("value", "base", "expected"), [(110, 100, "up"), (90, 100, "down"), (101, 100, "flat"), (99, 100, "flat"), (5, 0, "up"), (0, 0, "flat")]
)
def test_direction_uses_a_two_percent_tolerance(value, base, expected):
    assert baselines.direction(value, base) == expected


@pytest.mark.parametrize(
    ("marker", "lower_is_better", "expected"),
    [("down", True, "good"), ("up", True, "bad"), ("up", False, "good"), ("down", False, "bad"), ("flat", True, None), ("up", None, None), (None, True, None)],
)
def test_favourable_depends_on_which_direction_is_better(marker, lower_is_better, expected):
    assert baselines.favourable(marker, lower_is_better) == expected


@given(points=daily_series(), window=st.integers(1, 10))
@settings(max_examples=150)
def test_each_rolling_mean_lies_within_its_window(points, window):
    days = [DAY - timedelta(days=i) for i in range(20)]
    means = baselines.rolling_mean(points, days, window)

    for day, mean in zip(days, means, strict=True):
        values = [points[day - timedelta(days=i)] for i in range(window) if (day - timedelta(days=i)) in points]
        if not values:
            assert mean is None
        else:
            assert min(values) - 1e-9 <= mean <= max(values) + 1e-9


# --- Sleep consistency ----------------------------------------------------------------------------


def test_clock_spread_is_none_with_fewer_than_three_times_and_zero_for_identical_times():
    assert baselines.clock_spread([1380, 1400]) is None
    assert baselines.clock_spread([1380, 1380, 1380]) == 0.0


def test_times_around_midnight_count_as_close_together():
    assert baselines.clock_spread([1430, 5, 1435, 0]) < 20  # 23:50, 00:05, 23:55, 00:00
    assert baselines.clock_spread([1380, 360, 1380]) > 150  # 23:00 vs 06:00 are far apart


@given(times=st.lists(st.integers(0, 1439), min_size=3, max_size=14), shift=st.integers(0, 1439))
@settings(max_examples=200)
def test_clock_spread_does_not_change_when_every_time_moves_by_the_same_amount(times, shift):
    # Moving every time by the same amount, without crossing the 18:00 origin, keeps the spread.
    origin = baselines.CLOCK_ORIGIN_MIN
    relative = [(t - origin) % 1440 for t in times]
    room = 1439 - max(relative)
    delta = shift % (room + 1)
    moved = [(origin + r + delta) % 1440 for r in relative]

    assert baselines.clock_spread(moved) == pytest.approx(baselines.clock_spread(times), abs=1e-6)
