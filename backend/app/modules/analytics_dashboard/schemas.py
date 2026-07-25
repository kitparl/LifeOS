"""Pydantic schemas for the Analytics Dashboard module."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SeriesPoint(BaseModel):
    label: str
    value: float


class TimeSeries(BaseModel):
    key: str
    label: str
    points: list[SeriesPoint] = Field(default_factory=list)


class HeatmapCell(BaseModel):
    date: str
    value: float
    completed: bool = False


class PlaceholderField(BaseModel):
    status: Literal["coming_soon", "ready"] = "coming_soon"
    value: Any | None = None
    message: str = "Coming Soon"


class KpiCard(BaseModel):
    id: str
    title: str
    value: float | int | str
    unit: str | None = None
    subtitle: str | None = None
    trend: float | None = None


class AnalyticsOverview(BaseModel):
    life_score: float
    todays_tasks: int
    completed_tasks: int
    goal_progress: float
    habit_score: float
    focus_time_hours: float
    focus_time_label: str = "planned"
    journal_streak: int
    mood_score: float | None = None
    upcoming_events: list[dict[str, Any]] = Field(default_factory=list)
    recent_activity: list[dict[str, Any]] = Field(default_factory=list)
    kpis: list[KpiCard] = Field(default_factory=list)
    range_days: int = 30


class ProductivityAnalytics(BaseModel):
    daily_tasks: TimeSeries
    weekly_tasks: TimeSeries
    monthly_tasks: TimeSeries
    task_completion: list[SeriesPoint]
    overdue_tasks: int
    focus_hours: float
    deep_work_hours: float
    focus_label: str = "planned"
    category_distribution: list[SeriesPoint]
    calendar_heatmap: list[HeatmapCell]
    range_days: int = 30


class GoalItemAnalytics(BaseModel):
    id: str
    title: str
    progress: int
    status: str
    remaining_tasks: int
    milestones_total: int
    milestones_done: int
    velocity: float
    burndown: list[SeriesPoint] = Field(default_factory=list)
    completion_forecast: PlaceholderField = Field(default_factory=PlaceholderField)
    risk_indicator: PlaceholderField = Field(default_factory=PlaceholderField)


class GoalAnalytics(BaseModel):
    goals: list[GoalItemAnalytics] = Field(default_factory=list)
    avg_progress: float = 0.0
    avg_velocity: float = 0.0
    range_days: int = 90


class HabitItemAnalytics(BaseModel):
    id: str
    name: str
    current_streak: int
    longest_streak: int
    consistency_pct: float
    weekly_completion: float
    monthly_completion: float


class HabitAnalytics(BaseModel):
    habits: list[HabitItemAnalytics] = Field(default_factory=list)
    current_streak_max: int = 0
    longest_streak_max: int = 0
    consistency_avg: float = 0.0
    weekly_completion_avg: float = 0.0
    monthly_completion_avg: float = 0.0
    heatmap: list[HeatmapCell] = Field(default_factory=list)
    best_habit: str | None = None
    worst_habit: str | None = None
    range_days: int = 90


class JournalAnalytics(BaseModel):
    mood_trend: list[TimeSeries] = Field(default_factory=list)
    journal_frequency: TimeSeries
    word_count_total: int = 0
    word_count_series: TimeSeries
    writing_streak: int = 0
    sentiment: PlaceholderField = Field(default_factory=PlaceholderField)
    emotion: PlaceholderField = Field(default_factory=PlaceholderField)
    range_days: int = 90


class AiInsightBlock(BaseModel):
    period: Literal["daily", "weekly", "monthly", "predictions"]
    status: Literal["coming_soon", "ready"] = "coming_soon"
    title: str
    items: list[str] = Field(default_factory=list)
    message: str = "AI Insights coming soon"


class AiInsightsResponse(BaseModel):
    daily: AiInsightBlock
    weekly: AiInsightBlock
    monthly: AiInsightBlock
    predictions: AiInsightBlock


class WidgetDescriptor(BaseModel):
    id: str
    title: str
    icon: str
    type: Literal["kpi", "chart", "list", "placeholder"]
    endpoint: str
    refresh_interval: int = 60
    component: str
