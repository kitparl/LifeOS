from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.health.metrics import validate_measurement, validate_values

HealthRange = Literal["7d", "30d", "90d", "1y"]
MeasurementKind = Literal["weight", "body_comp", "blood_pressure"]


class MetricInfo(BaseModel):
    key: str
    label: str
    unit: str
    group: str
    kind: str
    min: float
    max: float
    lower_is_better: bool | None = None
    today: bool = False


class HealthDayInput(BaseModel):
    """Values to set on the manual row of a day: a value replaces, null clears, a missing key is untouched."""

    values: dict[str, object] = Field(max_length=40)

    @field_validator("values")
    @classmethod
    def _check(cls, values: dict[str, object]) -> dict[str, object]:
        return validate_values(values)


class HealthDayResponse(BaseModel):
    day: date
    values: dict[str, int | float]
    sources: dict[str, str]


class TodayMetric(BaseModel):
    key: str
    label: str
    unit: str
    value: int | float | None
    avg_7d: float | None = None
    avg_30d: float | None = None
    marker: Literal["up", "down", "flat"] | None = None
    favourable: Literal["good", "bad"] | None = None
    needs_more_data: bool = False


class HealthTodayResponse(BaseModel):
    day: date | None
    is_today: bool
    metrics: list[TodayMetric]


class MetricPoint(BaseModel):
    day: date
    value: float | None


class MetricSeriesResponse(BaseModel):
    key: str
    label: str
    unit: str
    range: HealthRange
    start: date
    end: date
    points: list[MetricPoint]
    rolling: list[MetricPoint]
    average: float | None
    minimum: float | None
    maximum: float | None


class SleepConsistency(BaseModel):
    nights: int
    bed_time_sd_min: float | None
    wake_time_sd_min: float | None


class SleepResponse(BaseModel):
    range: HealthRange
    start: date
    end: date
    nights: list[HealthDayResponse]
    consistency: SleepConsistency


class MeasurementCreate(BaseModel):
    kind: MeasurementKind
    measured_at: datetime | None = None
    values: dict[str, object] = Field(max_length=10)

    @model_validator(mode="after")
    def _check_values(self) -> Self:
        self.values = validate_measurement(self.kind, self.values)
        return self


class MeasurementResponse(BaseModel):
    id: str
    kind: str
    measured_at: datetime
    values: dict[str, float]
    source: str
