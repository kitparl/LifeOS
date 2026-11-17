"""Map Garmin Personal API health responses to the provider-neutral health contracts.

Pure functions. Field names come from real responses.
A missing, malformed or out-of-range value is dropped, never fatal: one odd field must not lose a day.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from app.modules.health.contracts import ParsedHealthDay, ParsedMeasurement
from app.modules.health.metrics import METRIC_BY_KEY, Number, validate_value

DayValues = dict[str, Number]


def _get(data: Any, *path: str) -> Any:
    for key in path:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _keep(values: DayValues, key: str, value: Any, *, scale: float = 1.0) -> None:
    """Store a value only if it is a number that passes the metric catalogue's checks."""
    number = _number(value)
    if number is None:
        return
    number *= scale
    spec = METRIC_BY_KEY[key]
    candidate: Number = round(number) if spec.kind in ("int", "clock") else round(number, 2)
    try:
        clean = validate_value(spec, candidate)
    except ValueError:
        return
    if clean is not None:
        values[key] = clean


def _calendar_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _clock_minutes(local_epoch_ms: Any) -> int | None:
    """Garmin's '...TimestampLocal' epoch values are local wall-clock time stored as if it were UTC."""
    number = _number(local_epoch_ms)
    if number is None:
        return None
    moment = datetime.fromtimestamp(number / 1000, tz=timezone.utc)
    return moment.hour * 60 + moment.minute


def summary_days(body: Any) -> dict[date, DayValues]:
    """`/usersummary-service/v2/dailysummaries`: activity, heart rate, stress, Body Battery, breathing."""
    days: dict[date, DayValues] = {}
    for item in _get(body, "data") or []:
        day = _calendar_date(_get(item, "calendarDate"))
        if day is None:
            continue
        values: DayValues = {}
        _keep(values, "steps", _get(item, "movement", "steps", "value"))
        _keep(values, "distance_km", _get(item, "movement", "steps", "distanceInMeters"), scale=0.001)
        _keep(values, "floors", _get(item, "movement", "floorsAscended", "value"))
        _keep(values, "active_calories", _get(item, "calories", "burnedActive"))
        _keep(values, "total_calories", _get(item, "calories", "burnedTotal"))
        _keep(values, "min_hr", _get(item, "heartRate", "minValue"))
        _keep(values, "max_hr", _get(item, "heartRate", "maxValue"))
        _keep(values, "resting_hr", _get(item, "heartRate", "restingValue"))
        _keep(values, "intensity_min_moderate", _get(item, "intensityMinutes", "moderate"))
        _keep(values, "intensity_min_vigorous", _get(item, "intensityMinutes", "vigorous"))
        _keep(values, "stress_avg", _get(item, "stress", "avgLevel"))
        _keep(values, "stress_max", _get(item, "stress", "maxLevel"))
        _keep(values, "body_battery_high", _get(item, "bodyBattery", "maxValue"))
        _keep(values, "body_battery_low", _get(item, "bodyBattery", "minValue"))
        _keep(values, "respiration_avg", _get(item, "respiration", "avgValue"))
        days[day] = values
    return days


def sleep_values(body: Any) -> DayValues:
    """`/sleep-service/sleep/dailySleep` for one date (the date the user woke up)."""
    values: DayValues = {}
    if _number(_get(body, "sleepTimeSeconds")) is None:
        return values  # no sleep recorded for this date
    minute = 1 / 60
    _keep(values, "sleep_total_min", _get(body, "sleepTimeSeconds"), scale=minute)
    _keep(values, "sleep_deep_min", _get(body, "deepSleepSeconds"), scale=minute)
    _keep(values, "sleep_light_min", _get(body, "lightSleepSeconds"), scale=minute)
    _keep(values, "sleep_rem_min", _get(body, "remSleepSeconds"), scale=minute)
    _keep(values, "sleep_awake_min", _get(body, "awakeSleepSeconds"), scale=minute)
    _keep(values, "sleep_score", _get(body, "sleepScores", "overall", "value"))
    _keep(values, "bed_time_min", _clock_minutes(_get(body, "sleepStartTimestampLocal")))
    _keep(values, "wake_time_min", _clock_minutes(_get(body, "sleepEndTimestampLocal")))
    return values


def hrv_days(body: Any) -> dict[date, DayValues]:
    """`/hrv-service/hrv/daily/{start}/{end}`: overnight average per date."""
    days: dict[date, DayValues] = {}
    for item in _get(body, "hrvSummaries") or []:
        day = _calendar_date(_get(item, "calendarDate"))
        if day is None:
            continue
        values: DayValues = {}
        _keep(values, "hrv_ms", _get(item, "lastNightAvg"))
        days[day] = values
    return days


def spo2_values(body: Any) -> DayValues:
    """`/wellness-service/wellness/daily/spo2acclimation/{date}`: empty when Pulse Ox is off."""
    values: DayValues = {}
    _keep(values, "spo2_avg", _get(body, "averageSpO2"))
    _keep(values, "spo2_min", _get(body, "lowestSpO2"))
    return values


def merge_days(*sources: dict[date, DayValues]) -> list[ParsedHealthDay]:
    """One day per date with every value found for it; dates without any value are left out."""
    merged: dict[date, DayValues] = {}
    for source in sources:
        for day, values in source.items():
            merged.setdefault(day, {}).update(values)
    return [ParsedHealthDay(day=day, values=dict(values)) for day, values in sorted(merged.items()) if values]


def weight_measurements(body: Any) -> list[ParsedMeasurement]:
    """`/weight-service/weight/range/...`: weight in grams; body fat and muscle mass when a scale sends them."""
    out: list[ParsedMeasurement] = []
    for summary in _get(body, "dailyWeightSummaries") or []:
        for entry in _get(summary, "allWeightMetrics") or []:
            sample = _get(entry, "samplePk")
            stamp = _number(_get(entry, "date"))
            grams = _number(_get(entry, "weight"))
            if sample is None or stamp is None or grams is None:
                continue
            measured_at = datetime.fromtimestamp(stamp / 1000, tz=timezone.utc)
            out.append(ParsedMeasurement("weight", measured_at, {"weight_kg": round(grams / 1000, 2)}, f"{sample}"))
            body_comp: dict[str, float] = {}
            fat, muscle, bmi = (_number(_get(entry, k)) for k in ("bodyFat", "muscleMass", "bmi"))
            if fat is not None:
                body_comp["body_fat_pct"] = round(fat, 1)
            if muscle is not None:
                body_comp["muscle_mass_kg"] = round(muscle / 1000, 2)
            if body_comp and bmi is not None:
                body_comp["bmi"] = round(bmi, 1)
            if body_comp:
                out.append(ParsedMeasurement("body_comp", measured_at, body_comp, f"{sample}:body"))
    return out
