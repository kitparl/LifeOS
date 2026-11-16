"""The metric catalogue: the single source of truth for what a health day can hold.

Keys equal the `health_days` column names. Validation, the API allowlist and the labels shown in
the UI all come from here.
"""

import math
from dataclasses import dataclass
from typing import Literal

MetricKind = Literal["int", "float", "clock"]


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    unit: str
    group: str
    kind: MetricKind
    min: float
    max: float
    # True: lower is better (resting heart rate); False: higher is better; None: neither direction is better.
    lower_is_better: bool | None = None
    today: bool = False  # shown on the Today view


METRICS: tuple[MetricSpec, ...] = (
    MetricSpec("sleep_total_min", "Sleep", "min", "sleep", "int", 0, 1440, False, today=True),
    MetricSpec("sleep_deep_min", "Deep sleep", "min", "sleep", "int", 0, 1440, False),
    MetricSpec("sleep_light_min", "Light sleep", "min", "sleep", "int", 0, 1440),
    MetricSpec("sleep_rem_min", "REM sleep", "min", "sleep", "int", 0, 1440, False),
    MetricSpec("sleep_awake_min", "Awake in bed", "min", "sleep", "int", 0, 1440, True),
    MetricSpec("sleep_score", "Sleep score", "", "sleep", "int", 0, 100, False),
    MetricSpec("bed_time_min", "Bed time", "", "sleep", "clock", 0, 1439),
    MetricSpec("wake_time_min", "Wake time", "", "sleep", "clock", 0, 1439),
    MetricSpec("resting_hr", "Resting heart rate", "bpm", "heart", "int", 20, 150, True, today=True),
    MetricSpec("min_hr", "Lowest heart rate", "bpm", "heart", "int", 20, 250, True),
    MetricSpec("max_hr", "Highest heart rate", "bpm", "heart", "int", 20, 250),
    MetricSpec("avg_hr", "Average heart rate", "bpm", "heart", "int", 20, 250),
    MetricSpec("hrv_ms", "HRV (overnight)", "ms", "heart", "float", 1, 300, False, today=True),
    MetricSpec("stress_avg", "Average stress", "", "stress", "int", 0, 100, True, today=True),
    MetricSpec("stress_max", "Peak stress", "", "stress", "int", 0, 100, True),
    MetricSpec("body_battery_high", "Body Battery (high)", "", "stress", "int", 0, 100, False, today=True),
    MetricSpec("body_battery_low", "Body Battery (low)", "", "stress", "int", 0, 100, False),
    MetricSpec("steps", "Steps", "", "activity", "int", 0, 200_000, False),
    MetricSpec("distance_km", "Distance", "km", "activity", "float", 0, 500),
    MetricSpec("floors", "Floors climbed", "", "activity", "int", 0, 1000),
    MetricSpec("active_calories", "Active calories", "kcal", "activity", "int", 0, 20_000),
    MetricSpec("total_calories", "Total calories", "kcal", "activity", "int", 0, 30_000),
    MetricSpec("intensity_min_moderate", "Moderate intensity", "min", "activity", "int", 0, 1440),
    MetricSpec("intensity_min_vigorous", "Vigorous intensity", "min", "activity", "int", 0, 1440),
    MetricSpec("respiration_avg", "Respiration", "br/min", "breathing", "float", 4, 60),
    MetricSpec("spo2_avg", "Blood oxygen (average)", "%", "breathing", "float", 50, 100, False),
    MetricSpec("spo2_min", "Blood oxygen (lowest)", "%", "breathing", "float", 50, 100, False),
    MetricSpec("vo2_max", "VO2 max", "", "fitness", "float", 10, 100, False),
)

METRIC_BY_KEY: dict[str, MetricSpec] = {m.key: m for m in METRICS}
TODAY_KEYS: tuple[str, ...] = tuple(m.key for m in METRICS if m.today)
SLEEP_KEYS: tuple[str, ...] = tuple(m.key for m in METRICS if m.group == "sleep")

Number = int | float


def validate_value(spec: MetricSpec, value: object) -> Number | None:
    """The value for one metric, or None to clear it. Raises ValueError with a user-safe message."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{spec.label} must be a number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{spec.label} must be a finite number")
    if spec.kind in ("int", "clock"):
        if isinstance(value, float):
            if not value.is_integer():
                raise ValueError(f"{spec.label} must be a whole number")
            value = int(value)
    else:
        value = float(value)
    if not spec.min <= value <= spec.max:
        raise ValueError(f"{spec.label} must be between {spec.min:g} and {spec.max:g}")
    return value


def validate_values(values: dict[str, object]) -> dict[str, Number | None]:
    """Validate a day's values against the catalogue (unknown keys, types and ranges)."""
    clean: dict[str, Number | None] = {}
    for key, value in values.items():
        spec = METRIC_BY_KEY.get(key)
        if spec is None:
            raise ValueError("Unknown health metric")
        clean[key] = validate_value(spec, value)
    return clean


@dataclass(frozen=True)
class MeasurementSpec:
    fields: dict[str, tuple[float, float]]
    required: tuple[str, ...] = ()
    at_least_one: bool = False


MEASUREMENT_KINDS: dict[str, MeasurementSpec] = {
    "weight": MeasurementSpec({"weight_kg": (20, 400)}, required=("weight_kg",)),
    "body_comp": MeasurementSpec(
        {"body_fat_pct": (1, 80), "muscle_mass_kg": (5, 200), "bmi": (8, 80)}, at_least_one=True
    ),
    "blood_pressure": MeasurementSpec(
        {"systolic": (50, 260), "diastolic": (30, 160), "pulse": (20, 250)}, required=("systolic", "diastolic")
    ),
}


def validate_measurement(kind: str, values: dict[str, object]) -> dict[str, float]:
    spec = MEASUREMENT_KINDS.get(kind)
    if spec is None:
        raise ValueError("Unknown measurement kind")
    clean: dict[str, float] = {}
    for key, value in values.items():
        bounds = spec.fields.get(key)
        if bounds is None:
            raise ValueError("Unknown value for this measurement")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{key} must be a number")
        if not bounds[0] <= value <= bounds[1]:
            raise ValueError(f"{key} must be between {bounds[0]:g} and {bounds[1]:g}")
        clean[key] = float(value)
    for key in spec.required:
        if key not in clean:
            raise ValueError(f"{key} is required")
    if spec.at_least_one and not clean:
        raise ValueError("Enter at least one value")
    return clean
