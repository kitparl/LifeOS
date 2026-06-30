from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.service import CalendarService
from app.modules.dashboard.schemas import (
    CalendarPreviewItem,
    DashboardSummaryResponse,
    GoalProgressItem,
    HabitTodayItem,
    NotificationItem,
    QuickActionItem,
    RunningProgress,
    TaskTodayItem,
)
from app.modules.goals.repository import GoalRepository
from app.modules.habits.service import HabitService
from app.modules.notifications.service import NotificationService
from app.modules.running.service import RunningService
from app.modules.tasks.repository import TaskRepository


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.goals = GoalRepository(db)
        self.tasks = TaskRepository(db)
        self.habits = HabitService(db)
        self.running = RunningService(db)
        self.calendar = CalendarService(db)
        self.notifications = NotificationService(db)

    async def get_summary(self, user_id: str) -> DashboardSummaryResponse:
        active_goals = await self.goals.get_active_for_dashboard(user_id)
        goals_progress = [
            GoalProgressItem(id=g.id, title=g.title, percent=g.progress) for g in active_goals
        ]
        today_tasks = await self.tasks.get_today_for_dashboard(user_id)
        tasks_today = [
            TaskTodayItem(id=t.id, title=t.title, due_at=t.due_date, priority=t.priority)
            for t in today_tasks
        ]
        habit_items = await self.habits.get_dashboard_items(user_id)
        habits_today = [
            HabitTodayItem(id=h_id, name=name, completed=completed) for h_id, name, completed in habit_items
        ]
        running_data = await self.running.get_dashboard_progress(user_id)
        running_progress = (
            RunningProgress(
                weekly_km=running_data["weekly_km"],
                goal_km=running_data["goal_km"],
                last_run=running_data["last_run"],
            )
            if running_data
            else None
        )
        calendar_items = await self.calendar.get_dashboard_preview(user_id)
        calendar_preview = [
            CalendarPreviewItem(id=eid, title=title, starts_at=starts_at)
            for eid, title, starts_at in calendar_items
        ]
        notif_items = await self.notifications.get_dashboard_notifications(user_id)
        notifications = [
            NotificationItem(
                id=n.id,
                message=n.message,
                route=n.route,
                is_read=n.is_read,
                created_at=n.created_at,
            )
            for n in notif_items
        ]
        return DashboardSummaryResponse(
            sync_status="synced",
            pending_sync_count=0,
            tasks_today=tasks_today,
            habits_today=habits_today,
            goals_progress=goals_progress,
            running_progress=running_progress,
            calendar_preview=calendar_preview,
            notifications=notifications,
            recent_activity=[],
            quick_actions=[
                QuickActionItem(id="add_goal", label="New Goal", route="/goals/new", enabled=True),
                QuickActionItem(id="add_task", label="New Task", route="/tasks/new", enabled=True),
                QuickActionItem(id="add_habit", label="New Habit", route="/habits/new", enabled=True),
                QuickActionItem(id="log_run", label="Log Run", route="/running/new", enabled=True),
                QuickActionItem(id="add_event", label="New Event", route="/calendar/new", enabled=True),
                QuickActionItem(id="add_journal", label="New Journal", route="/journal/new", enabled=True),
                QuickActionItem(id="add_word", label="Add Word", route="/communication/vocabulary/new", enabled=True),
                QuickActionItem(id="add_qa", label="New Q&A", route="/qa/new", enabled=True),
                QuickActionItem(id="add_wishlist", label="New Wishlist", route="/wishlist/new", enabled=True),
                QuickActionItem(id="export_data", label="Export Data", route="/export", enabled=True),
                QuickActionItem(id="upload_file", label="Upload File", route="/files", enabled=True),
            ],
        )
