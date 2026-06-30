from datetime import datetime

from pydantic import BaseModel, Field


class AutomationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    trigger_type: str
    condition_json: str | None = None
    action_type: str = "notify"
    action_config_json: str | None = None
    enabled: bool = True


class AutomationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    trigger_type: str | None = None
    condition_json: str | None = None
    action_type: str | None = None
    action_config_json: str | None = None
    enabled: bool | None = None


class AutomationResponse(BaseModel):
    id: str
    name: str
    trigger_type: str
    condition_json: str | None
    action_type: str
    action_config_json: str | None
    enabled: bool
    last_run_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AutomationRunResult(BaseModel):
    rule_id: str
    rule_name: str
    triggered: bool
    action_taken: str | None = None
    message: str | None = None


class AutomationEvaluateResponse(BaseModel):
    evaluated: int
    triggered: int
    results: list[AutomationRunResult]
