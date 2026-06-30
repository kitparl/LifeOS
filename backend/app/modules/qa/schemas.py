from datetime import datetime

from pydantic import BaseModel, Field


class QACreate(BaseModel):
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    tags: list[str] = []
    linked_goal_id: str | None = None
    linked_journal_id: str | None = None


class QAUpdate(BaseModel):
    question: str | None = Field(default=None, min_length=1)
    answer: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None
    linked_goal_id: str | None = None
    linked_journal_id: str | None = None


class QAVersionResponse(BaseModel):
    id: str
    version_number: int
    answer: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QAListItem(BaseModel):
    id: str
    question: str
    current_answer: str
    tags: list[str]
    updated_at: datetime


class QAResponse(BaseModel):
    id: str
    question: str
    current_answer: str
    tags: list[str]
    linked_goal_id: str | None
    linked_journal_id: str | None
    ai_summary: str | None
    created_at: datetime
    updated_at: datetime
    versions: list[QAVersionResponse] = []
