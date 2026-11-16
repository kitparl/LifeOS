"""Values exchanged with whatever feeds synced activities into running.

Defined here so running never imports the activity log or a provider package.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SyncedRunInput:
    activity_id: str
    source: str
    start_time_utc: datetime
    timezone: str | None
    distance_m: float
    # Timer (moving) time; elapsed includes pauses.
    timer_seconds: float
    elapsed_seconds: float


@dataclass(frozen=True)
class SyncRunResult:
    # None when the activity is not usable as a run (no distance or no time).
    run_id: str | None
    created: bool
    matched_manual: bool


@dataclass(frozen=True)
class RevertResult:
    runs_deleted: int
    runs_restored: int
    races_detached: int
