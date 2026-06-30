from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

RaceDistanceType = Literal["5k", "10k", "15k", "half_marathon", "marathon", "other"]


class RunCreate(BaseModel):
    run_date: date
    distance_km: float = Field(gt=0, le=500)
    duration_seconds: int = Field(gt=0, le=86400)
    weather: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class RunUpdate(BaseModel):
    run_date: date | None = None
    distance_km: float | None = Field(default=None, gt=0, le=500)
    duration_seconds: int | None = Field(default=None, gt=0, le=86400)
    weather: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class RunListItem(BaseModel):
    id: str
    run_date: date
    distance_km: float
    duration_seconds: int
    pace_min_per_km: float
    weather: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunResponse(BaseModel):
    id: str
    run_date: date
    distance_km: float
    duration_seconds: int
    pace_min_per_km: float
    weather: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    race_date: date
    distance_type: RaceDistanceType = "other"
    distance_km: float | None = Field(default=None, gt=0, le=500)
    location: str | None = Field(default=None, max_length=200)
    registered: bool = False
    notes: str | None = None


class RaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    race_date: date | None = None
    distance_type: RaceDistanceType | None = None
    distance_km: float | None = Field(default=None, gt=0, le=500)
    location: str | None = Field(default=None, max_length=200)
    registered: bool | None = None
    notes: str | None = None


class RaceResponse(BaseModel):
    id: str
    name: str
    race_date: date
    distance_type: str
    distance_km: float | None
    location: str | None
    registered: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunningSettingsUpdate(BaseModel):
    weekly_goal_km: float | None = Field(default=None, gt=0, le=500)
    target_marathon_date: date | None = None
    target_half_marathon_date: date | None = None
    target_marathon_name: str | None = Field(default=None, max_length=200)


class RunningSettingsResponse(BaseModel):
    weekly_goal_km: float
    target_marathon_date: date | None
    target_half_marathon_date: date | None
    target_marathon_name: str | None

    model_config = {"from_attributes": True}


class PersonalBest(BaseModel):
    distance_type: str
    label: str
    run_id: str | None
    run_date: date | None
    distance_km: float | None
    pace_min_per_km: float | None
    duration_seconds: int | None


class RunningStatsResponse(BaseModel):
    weekly_km: float
    weekly_goal_km: float
    total_runs: int
    total_km: float
    last_run_date: date | None
    personal_bests: list[PersonalBest]
