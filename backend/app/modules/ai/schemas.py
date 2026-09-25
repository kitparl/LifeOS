from datetime import datetime

from app.modules.ai.adapters.base import MODEL_ID_PATTERN
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
    # False when the selected provider is no longer connected/enabled.
    available: bool = True


class UseCaseResponse(BaseModel):
    use_case: str
    display_name: str
    capability: str
    options: list[ModelOptionResponse]
    current: CurrentSelectionResponse | None = None


class UseCaseModelUpdate(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    model: str = Field(min_length=1, max_length=80, pattern=MODEL_ID_PATTERN)
    # Accept a model id that is not (yet) in the provider's cached catalog.
    custom: bool = False


class UseCaseHistoryItem(BaseModel):
    provider: str
    model: str
    effective_from: datetime
    effective_to: datetime | None = None


class AiSettings(BaseModel):
    """Per-user AI defaults (stored in user_preferences under "ai_settings")."""

    default_provider: str | None = Field(default=None, max_length=32)
    timeout_seconds: int = Field(default=120, ge=10, le=300)
    max_tokens: int = Field(default=1200, ge=256, le=8192)
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)
