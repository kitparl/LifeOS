from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ImportRange = Literal["12m", "all"]


class ImportFileError(BaseModel):
    name: str
    reason: str


class ImportJobResponse(BaseModel):
    id: str
    status: str
    range_mode: str
    files_found: int
    created: int
    duplicates: int
    outside_range: int
    not_activity: int
    failed: int
    runs_created: int
    runs_matched: int
    errors: list[ImportFileError] = []
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ImportedSummary(BaseModel):
    activities: int
    runs_created: int
    runs_merged_into_manual: int
    health_days: int = 0


class DeleteImportedResult(BaseModel):
    activities_deleted: int
    runs_deleted: int
    runs_restored: int
    races_detached: int
    files_deleted: int
    health_days_deleted: int = 0
