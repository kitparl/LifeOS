from datetime import datetime

from pydantic import BaseModel


class LapOut(BaseModel):
    index: int
    start_offset_s: float
    duration_s: float
    distance_m: float
    avg_hr: int | None = None
    avg_cadence: float | None = None
    elevation_gain_m: float | None = None


class SplitOut(BaseModel):
    index: int
    distance_m: float
    duration_s: float
    pace_s_per_km: float | None = None
    avg_hr: float | None = None
    elevation_change_m: float | None = None
    avg_cadence: float | None = None


class ActivityDetail(BaseModel):
    id: str
    source: str
    sport: str
    start_time_utc: datetime
    timezone: str | None = None
    elapsed_seconds: float
    timer_seconds: float
    distance_m: float
    elevation_gain_m: float | None = None
    avg_hr: int | None = None
    max_hr: int | None = None
    avg_cadence: float | None = None
    max_speed_mps: float | None = None
    calories: int | None = None
    device: str | None = None
    training_effect_aerobic: float | None = None
    training_effect_anaerobic: float | None = None
    laps: list[LapOut] = []
    splits: list[SplitOut] = []
    has_route: bool = False
    has_series: bool = False
    has_original_file: bool = False


class ActivitySeriesResponse(BaseModel):
    sample_count: int
    time_s: list[int]
    distance_m: list[float | None] | None = None
    heart_rate: list[int | None] | None = None
    cadence: list[float | None] | None = None
    altitude_m: list[float | None] | None = None
    speed_mps: list[float | None] | None = None
    route: list[tuple[float, float]] = []
