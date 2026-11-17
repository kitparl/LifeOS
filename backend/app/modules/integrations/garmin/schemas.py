from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

ImportRange = Literal["12m", "all"]


class ImportFileError(BaseModel):
    name: str
    reason: str


class ImportJobResponse(BaseModel):
    id: str
    status: str
    range_mode: str
    origin: str = "upload"
    files_found: int
    created: int
    duplicates: int
    outside_range: int
    not_activity: int
    failed: int
    runs_created: int
    runs_matched: int
    health_days: int = 0
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


class GarminKeyUpdate(BaseModel):
    api_key: str = Field(min_length=8, max_length=4096)


class GarminConnectionStatus(BaseModel):
    """Public status. Never includes the key or a token."""

    connected: bool
    key_masked: str = ""
    status: str = "disconnected"
    last_sync_at: datetime | None = None
    last_sync_message: str | None = None
    last_sync_ok: bool | None = None
    synced_through: date | None = None
