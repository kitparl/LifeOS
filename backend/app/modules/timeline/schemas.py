from datetime import datetime
from typing import Literal

from pydantic import BaseModel

TimelineSourceKey = Literal[
    "calendar", "running", "travel", "tasks", "journal", "finance", "wishlist", "routines"
]


class TimelineSource(BaseModel):
    key: TimelineSourceKey
    label: str
    default_enabled: bool


class TimelineItem(BaseModel):
    # Unique across sources: "<kind>:<entity id>" (recurring occurrences keep their own suffix).
    id: str
    source: TimelineSourceKey
    kind: str
    title: str
    subtitle: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    all_day: bool = False
    status: str | None = None
    route: str | None = None
