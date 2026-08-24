from datetime import datetime

from pydantic import BaseModel, Field


class AiStatusResponse(BaseModel):
    enabled: bool
    provider: str
    indexed_chunks: int
    embedding_chunks: int


class AiChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AiSourceItem(BaseModel):
    source_type: str
    source_id: str
    title: str
    route: str
    snippet: str
    score: float


class AiChatResponse(BaseModel):
    reply: str
    sources: list[AiSourceItem]


class AiIndexResponse(BaseModel):
    indexed: int
    embedded: int


class ModelOptionResponse(BaseModel):
    provider: str
    model: str
    display_name: str
    available: bool = True


class CurrentSelectionResponse(BaseModel):
    provider: str
    model: str
    updated_at: datetime | None = None


class UseCaseResponse(BaseModel):
    use_case: str
    display_name: str
    options: list[ModelOptionResponse]
    current: CurrentSelectionResponse | None = None


class UseCaseModelUpdate(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    model: str = Field(min_length=1, max_length=80)


class UseCaseHistoryItem(BaseModel):
    provider: str
    model: str
    effective_from: datetime
    effective_to: datetime | None = None
