"""Provider-neutral health data handed from an importer, and results of bulk operations."""

from dataclasses import dataclass, field
from datetime import date, datetime

SOURCE_MANUAL = "manual"
SOURCE_GARMIN = "garmin"


@dataclass(frozen=True)
class ParsedHealthDay:
    day: date
    values: dict[str, int | float | None] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedMeasurement:
    """One reading from an importer. `external_id` identifies it within its source, so re-imports update it."""

    kind: str
    measured_at: datetime
    values: dict[str, float]
    external_id: str


@dataclass(frozen=True)
class UpsertCounts:
    created: int = 0
    updated: int = 0
