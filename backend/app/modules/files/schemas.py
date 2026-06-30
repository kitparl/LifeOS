from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class FileUploadResponse(FileRecordResponse):
    pass
