from datetime import datetime

from pydantic import BaseModel


class ModuleCount(BaseModel):
    module: str
    count: int


class AnalyticsSummary(BaseModel):
    modules: list[ModuleCount]
    tasks_completed: int
    habits_logged_30d: int
    runs_30d: int
    journal_entries_30d: int
    learning_in_progress: int
    finance_net: float


class ChartPoint(BaseModel):
    label: str
    value: float


class AnalyticsCharts(BaseModel):
    tasks_by_status: list[ChartPoint]
    expenses_by_category: list[ChartPoint]
    learning_by_type: list[ChartPoint]
