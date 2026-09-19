from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WritingCategory = Literal["linkedin", "blog", "essay", "notes", "hr_answer", "technical_answer"]
SpeakingCategory = Literal["hr", "technical", "elevator", "mock_interview"]


class WritingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    category: WritingCategory = "notes"


class WritingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    category: WritingCategory | None = None


class WritingResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SpeakingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1)
    response: str | None = None
    category: SpeakingCategory = "hr"
    notes: str | None = None


class SpeakingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    prompt: str | None = None
    response: str | None = None
    category: SpeakingCategory | None = None
    notes: str | None = None


class SpeakingResponse(BaseModel):
    id: str
    title: str
    prompt: str
    response: str | None
    category: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WritingIssueItem(BaseModel):
    location: str = ""
    problem_type: str = ""
    severity: str = "medium"
    original_text: str = ""
    explanation: str = ""
    suggestion: str = ""


class WritingEvaluationResponse(BaseModel):
    id: str
    writing_id: str
    evaluation_key: str
    provider: str
    model: str
    model_version: str | None = None
    prompt_version: str
    rubric_version: str
    evaluation_version: str
    overall_score: int
    dimensions: dict[str, int]
    strengths: list[str]
    issues: list[WritingIssueItem]
    suggestions: list[str]
    metrics: dict
    already_strong: bool = False
    truncated: bool = False
    truncation_note: str | None = None
    cached: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class WritingRewriteResponse(BaseModel):
    id: str
    writing_id: str
    rewrite_key: str
    provider: str
    model: str
    prompt_version: str
    suggested_text: str
    why_better: list[str]
    key_changes: list[str]
    truncated: bool = False
    truncation_note: str | None = None
    cached: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
