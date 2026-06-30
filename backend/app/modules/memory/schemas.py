from datetime import datetime

from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    memory_key: str = Field(min_length=1, max_length=120)
    memory_value: str = Field(min_length=1)
    category: str = "fact"
    importance: int = Field(default=3, ge=1, le=5)


class MemoryUpdate(BaseModel):
    memory_key: str | None = Field(default=None, min_length=1, max_length=120)
    memory_value: str | None = Field(default=None, min_length=1)
    category: str | None = None
    importance: int | None = Field(default=None, ge=1, le=5)


class MemoryResponse(BaseModel):
    id: str
    memory_key: str
    memory_value: str
    category: str
    importance: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemorySummary(BaseModel):
    total: int
    by_category: dict[str, int]
    top_preferences: list[MemoryResponse]
