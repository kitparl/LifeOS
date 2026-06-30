from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SyncStatus = Literal["synced", "syncing", "offline"]


class TaskTodayItem(BaseModel):
    id: str
    title: str
    due_at: datetime | None = None
    priority: str | None = None


class HabitTodayItem(BaseModel):
    id: str
    name: str
    completed: bool


class GoalProgressItem(BaseModel):
    id: str
    title: str
    percent: int


class RunningProgress(BaseModel):
    weekly_km: float
    goal_km: float
    last_run: str | None = None


class CalendarPreviewItem(BaseModel):
    id: str
    title: str
    starts_at: datetime


class NotificationItem(BaseModel):
    id: str
    message: str
    created_at: datetime


class ActivityItem(BaseModel):
    type: str
    label: str
    at: datetime


class QuickActionItem(BaseModel):
    id: str
    label: str
    route: str | None = None
    enabled: bool = False


class DashboardSummaryResponse(BaseModel):
    sync_status: SyncStatus
    pending_sync_count: int
    tasks_today: list[TaskTodayItem]
    habits_today: list[HabitTodayItem]
    goals_progress: list[GoalProgressItem]
    running_progress: RunningProgress | None
    calendar_preview: list[CalendarPreviewItem]
    notifications: list[NotificationItem]
    recent_activity: list[ActivityItem]
    quick_actions: list[QuickActionItem]
