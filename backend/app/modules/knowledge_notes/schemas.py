from datetime import datetime

from pydantic import BaseModel, Field


# ---- Sections ----
class SectionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    order_index: int | None = None


class SectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    order_index: int | None = None
    chapter_id: str | None = None


class SectionResponse(BaseModel):
    id: str
    chapter_id: str
    title: str
    content: str
    order_index: int
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- Chapters ----
class ChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    order_index: int | None = None


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    order_index: int | None = None


class ChapterResponse(BaseModel):
    id: str
    subject_id: str
    title: str
    order_index: int
    sections: list[SectionResponse] = []

    model_config = {"from_attributes": True}


# ---- Subjects ----
class SubjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=16)


class SubjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=16)
    order_index: int | None = None


class SubjectListItem(BaseModel):
    id: str
    title: str
    description: str | None
    icon: str | None
    order_index: int
    chapter_count: int
    section_count: int
    updated_at: datetime


class SubjectDetail(BaseModel):
    id: str
    title: str
    description: str | None
    icon: str | None
    order_index: int
    created_at: datetime
    updated_at: datetime
    chapters: list[ChapterResponse] = []
    archived_sections: list[SectionResponse] = []

    model_config = {"from_attributes": True}


# ---- Search ----
class SearchHit(BaseModel):
    section_id: str
    section_title: str
    chapter_id: str
    chapter_title: str
    subject_id: str
    subject_title: str
    snippet: str
