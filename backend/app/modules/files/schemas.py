from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FileRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_backend: str
    url: str
    module: str | None
    entity_id: str | None
    created_at: datetime
    checksum_sha256: str | None = None
    extension: str | None = None
    visibility: str = "private"


class FileUploadResponse(FileRecordResponse):
    pass


class DownloadTokenResponse(BaseModel):
    token: str
    expires_at: datetime


class FileVisibilityUpdate(BaseModel):
    visibility: str = Field(..., pattern="^(private|public)$")


class FileUsageResponse(BaseModel):
    used_bytes: int
    quota_bytes: int
    file_count: int


class PurgeResponse(BaseModel):
    purged: int
