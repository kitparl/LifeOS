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
