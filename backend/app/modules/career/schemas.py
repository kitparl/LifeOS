from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CareerProfileUpdate(BaseModel):
    resume_url: str | None = None
    github_username: str | None = None
    linkedin_url: str | None = None
    headline: str | None = None


class CareerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_url: str | None
    github_username: str | None
    linkedin_url: str | None
    headline: str | None
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    tech_stack: str | None = None
    url: str | None = None
    repo_url: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    tech_stack: str | None = None
    url: str | None = None
    repo_url: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    tech_stack: str | None
    url: str | None
    repo_url: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    status: str = "applied"
    applied_at: date | None = None
    interview_at: date | None = None
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = None
    applied_at: date | None = None
    interview_at: date | None = None
    notes: str | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company: str
    role: str
    status: str
    applied_at: date | None
    interview_at: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
