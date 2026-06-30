from pydantic import BaseModel


class PredictionItem(BaseModel):
    key: str
    label: str
    score: float
    level: str
    summary: str


class PredictionsSummary(BaseModel):
    running_readiness: PredictionItem
    burnout_risk: PredictionItem
    overspending_risk: PredictionItem
    learning_consistency: PredictionItem
    goal_completion_probability: PredictionItem
