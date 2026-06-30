from datetime import date, datetime

from pydantic import BaseModel, Field


class MoodUpsert(BaseModel):
    stress: int = Field(ge=1, le=5)
    confidence: int = Field(ge=1, le=5)
    motivation: int = Field(ge=1, le=5)
    happiness: int = Field(ge=1, le=5)
    notes: str | None = None


class MoodResponse(BaseModel):
    id: str
    log_date: date
    stress: int
    confidence: int
    motivation: int
    happiness: int
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MoodStats(BaseModel):
    days: int
    avg_stress: float
    avg_confidence: float
    avg_motivation: float
    avg_happiness: float
    recent: list[MoodResponse]
