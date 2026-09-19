from typing import Literal

from pydantic import BaseModel

PreviewType = Literal[
    "pdf", "image", "text", "csv", "markdown", "video", "audio", "unsupported"
]
PreviewStatus = Literal["ready", "processing", "failed"]


class PreviewInfoResponse(BaseModel):
    document_id: str
    file_name: str
    original_mime_type: str
    preview_type: PreviewType
    status: PreviewStatus
    preview_url: str | None
    download_url: str
    page_count: int | None = None
    error: str | None = None
