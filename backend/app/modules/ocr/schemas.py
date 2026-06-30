from datetime import datetime

from pydantic import BaseModel, Field


class OcrDocumentCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    doc_type: str = "document"
    text: str | None = None
    file_id: str | None = None


class OcrDocumentResponse(BaseModel):
    id: str
    file_id: str | None
    filename: str
    doc_type: str
    extracted_text: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
