"""Provider-neutral activity data handed from an importer to the activity log."""

from dataclasses import dataclass, field
from datetime import datetime

# Normalised sports (see ParsedActivity.sport). Only these become runs.
RUNNING_SPORTS = frozenset({"running", "trail_running", "treadmill_running", "track_running", "virtual_running"})


@dataclass(frozen=True)
class ParsedLap:
    index: int
    start_offset_s: float
    duration_s: float
    distance_m: float
    avg_hr: int | None = None
    avg_cadence: float | None = None
    elevation_gain_m: float | None = None


@dataclass(frozen=True)
class ParsedSeries:
    """Equal-length lists, one entry per recorded sample; None marks a missing value for that sample.

    A channel that never had a value is None instead of a list.
    """

    time_s: list[int]
    distance_m: list[float | None] | None = None
    lat: list[float | None] | None = None
    lon: list[float | None] | None = None
    altitude_m: list[float | None] | None = None
    heart_rate: list[int | None] | None = None
    cadence: list[float | None] | None = None
    speed_mps: list[float | None] | None = None
    extras: dict[str, list[float | None]] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedActivity:
    source: str  # "garmin"
    external_id: str  # stable id of the recording, so re-importing it is recognised
    sport: str  # "running", "trail_running", "cycling", ...
    start_time_utc: datetime
    elapsed_s: float
    timer_s: float
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
    laps: list[ParsedLap] = field(default_factory=list)
    series: ParsedSeries | None = None


@dataclass(frozen=True)
class OriginalFile:
    filename: str
    data: bytes


@dataclass(frozen=True)
class IngestResult:
    outcome: str  # "created" | "duplicate"
    activity_id: str
    run_id: str | None = None
    run_created: bool = False
    run_matched: bool = False


@dataclass(frozen=True)
class DeleteResult:
    activities_deleted: int = 0
    runs_deleted: int = 0
    runs_restored: int = 0
    races_detached: int = 0
    files_deleted: int = 0
