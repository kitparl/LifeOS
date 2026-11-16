"""Provider-neutral health data handed from an importer, and results of bulk operations."""

from dataclasses import dataclass, field
from datetime import date

SOURCE_MANUAL = "manual"
SOURCE_GARMIN = "garmin"


@dataclass(frozen=True)
class ParsedHealthDay:
    day: date
    values: dict[str, int | float | None] = field(default_factory=dict)


@dataclass(frozen=True)
class UpsertCounts:
    created: int = 0
    updated: int = 0
