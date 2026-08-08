from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.learning.models import (
    LEARNING_STATUSES,
    LEARNING_TYPES,
    RESOURCE_PRIORITY,
    RESOURCE_TYPES,
    TRACK_STATUSES,
)

TrackStatus = Literal["planned", "active", "completed", "paused"]
ResourceType = Literal["video", "playlist", "article", "docs", "course", "paper", "repo", "book"]
ResourcePriority = Literal["primary", "supporting", "optional"]


# --- Existing LearningItem schemas (extended) ---


class LearningCreate(BaseModel):
    item_type: str = "book"
    title: str = Field(min_length=1, max_length=200)
    provider: str | None = Field(default=None, max_length=120)
    url: str | None = Field(default=None, max_length=500)
    status: str = "planned"
    progress: int = Field(default=0, ge=0, le=100)
    target_date: date | None = None
    notes: str | None = None
    track_id: str | None = Field(default=None, max_length=36)
    sort_order: int = 0

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        if v not in LEARNING_TYPES:
            raise ValueError(f"item_type must be one of {LEARNING_TYPES}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in LEARNING_STATUSES:
            raise ValueError(f"status must be one of {LEARNING_STATUSES}")
        return v


class LearningUpdate(BaseModel):
    item_type: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    provider: str | None = Field(default=None, max_length=120)
    url: str | None = Field(default=None, max_length=500)
    status: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    target_date: date | None = None
    notes: str | None = None
    track_id: str | None = Field(default=None, max_length=36)
    sort_order: int | None = None


class LearningListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_type: str
    title: str
    provider: str | None
    status: str
    progress: int
    target_date: date | None
    track_id: str | None = None
    sort_order: int = 0
    updated_at: datetime


class LearningResponse(LearningListItem):
    url: str | None
    notes: str | None
    slug: str | None = None
    created_at: datetime


# --- Track ---


class TrackCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TrackStatus = "planned"
    start_date: date | None = None
    target_date: date | None = None
    weekly_hours_target: int = Field(default=11, ge=1, le=80)
    sort_order: int = 0


class TrackSeedRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str | None
    concept_id: str | None
    resource_type: str
    title: str
    url: str
    provider: str | None
    author: str | None
    duration_minutes: int | None
    priority: str
    sort_order: int
    is_consumed: bool
    notes: str | None
    last_verified_at: date | None


class ConceptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str
    slug: str
    title: str
    summary: str | None
    week_number: int | None
    estimated_minutes: int | None
    sort_order: int
    confidence: int
    can_explain: bool
    failure_modes_known: bool
    tradeoffs_known: bool
    artifact_url: str | None
    completed_at: datetime | None
    resources: list[ResourceResponse] = []
    inherited_resources: list[ResourceResponse] = []


class PhaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    track_id: str | None
    slug: str | None
    item_type: str
    title: str
    status: str
    progress: int
    sort_order: int
    concepts: list[ConceptResponse] = []
    resources: list[ResourceResponse] = []


class TrackListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    title: str
    description: str | None
    status: str
    start_date: date | None
    target_date: date | None
    weekly_hours_target: int
    sort_order: int
    created_at: datetime
    updated_at: datetime


class TrackDetail(TrackListItem):
    phases: list[PhaseResponse] = []


class TrackProgress(BaseModel):
    track_id: str
    percent_complete: float
    concepts_total: int
    concepts_gated: int
    hours_logged: float
    weekly_hours_target: int
    pace_hours_this_week: float
    study_streak_days: int


# --- Concept ---


class ConceptUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = None
    confidence: int | None = Field(default=None, ge=0, le=5)
    can_explain: bool | None = None
    failure_modes_known: bool | None = None
    tradeoffs_known: bool | None = None
    artifact_url: str | None = Field(default=None, max_length=500)
    completed_at: datetime | None = None


class ConceptListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str
    slug: str
    title: str
    summary: str | None
    week_number: int | None
    estimated_minutes: int | None
    sort_order: int
    confidence: int
    can_explain: bool
    failure_modes_known: bool
    tradeoffs_known: bool
    artifact_url: str | None
    completed_at: datetime | None


# --- Resource ---


class ResourceCreate(BaseModel):
    item_id: str | None = Field(default=None, max_length=36)
    concept_id: str | None = Field(default=None, max_length=36)
    resource_type: ResourceType = "article"
    title: str = Field(min_length=1, max_length=300)
    url: str = Field(min_length=1, max_length=1000)
    provider: str | None = Field(default=None, max_length=120)
    author: str | None = Field(default=None, max_length=120)
    duration_minutes: int | None = Field(default=None, ge=0)
    priority: ResourcePriority = "supporting"
    sort_order: int = 0
    notes: str | None = None

    @field_validator("resource_type")
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        if v not in RESOURCE_TYPES:
            raise ValueError(f"resource_type must be one of {RESOURCE_TYPES}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in RESOURCE_PRIORITY:
            raise ValueError(f"priority must be one of {RESOURCE_PRIORITY}")
        return v


class ResourceUpdate(BaseModel):
    is_consumed: bool | None = None
    notes: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    priority: ResourcePriority | None = None


# --- Session ---


class SessionCreate(BaseModel):
    item_id: str = Field(min_length=1, max_length=36)
    concept_id: str | None = Field(default=None, max_length=36)
    session_date: date
    minutes: int = Field(ge=1, le=24 * 60)
    confidence: int = Field(default=1, ge=1, le=5)
    can_explain: bool = False
    artifact_url: str | None = Field(default=None, max_length=500)
    notes: str | None = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str
    concept_id: str | None
    session_date: date
    minutes: int
    confidence: int
    can_explain: bool
    artifact_url: str | None
    notes: str | None
    created_at: datetime


class SessionStats(BaseModel):
    minutes_this_week: int
    minutes_total: int
    concepts_gated: int
    concepts_total: int
    pace_vs_target_hours: float | None
    study_streak_days: int


# --- Concept ↔ knowledge notes ---


class ConceptNoteCreate(BaseModel):
    """Attach a knowledge note to a concept.

    Provide exactly one entry point: an existing `section_id` to link, an existing
    `subject_id` to write into, or a `subject_title` to create a new subject.
    """

    section_id: str | None = Field(default=None, max_length=36)
    subject_id: str | None = Field(default=None, max_length=36)
    subject_title: str | None = Field(default=None, min_length=1, max_length=200)
    chapter_id: str | None = Field(default=None, max_length=36)
    chapter_title: str | None = Field(default=None, min_length=1, max_length=200)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str = ""

    @model_validator(mode="after")
    def validate_target(self) -> "ConceptNoteCreate":
        if not any([self.section_id, self.subject_id, self.subject_title, self.chapter_id]):
            raise ValueError("Provide section_id, subject_id, chapter_id or subject_title")
        return self


class ConceptNoteResponse(BaseModel):
    id: str
    concept_id: str
    section_id: str
    section_title: str
    snippet: str
    chapter_id: str
    chapter_title: str
    subject_id: str
    subject_title: str
    route: str
    updated_at: datetime
