from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

WritingCategory = Literal["linkedin", "blog", "essay", "notes", "hr_answer", "technical_answer"]
SpeakingCategory = Literal["hr", "technical", "elevator", "mock_interview"]


class VocabularyCreate(BaseModel):
    word: str = Field(min_length=1, max_length=120)
    meaning: str = Field(min_length=1)
    examples: str | None = None
    pronunciation: str | None = Field(default=None, max_length=120)
    synonyms: str | None = None
    mastery: int = Field(default=1, ge=1, le=5)
    notes: str | None = None


class VocabularyUpdate(BaseModel):
    word: str | None = Field(default=None, min_length=1, max_length=120)
    meaning: str | None = None
    examples: str | None = None
    pronunciation: str | None = Field(default=None, max_length=120)
    synonyms: str | None = None
    mastery: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class VocabularyResponse(BaseModel):
    id: str
    word: str
    meaning: str
    examples: str | None
    pronunciation: str | None
    synonyms: str | None
    mastery: int
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
