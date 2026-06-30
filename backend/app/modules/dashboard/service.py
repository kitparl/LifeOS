from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.schemas import (
    DashboardSummaryResponse,
    GoalProgressItem,
    HabitTodayItem,
    QuickActionItem,
    RunningProgress,
    TaskTodayItem,
)
from app.modules.goals.repository import GoalRepository
from app.modules.habits.service import HabitService
from app.modules.running.service import RunningService
from app.modules.tasks.repository import TaskRepository


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.goals = GoalRepository(db)
        self.tasks = TaskRepository(db)
        self.habits = HabitService(db)
        self.running = RunningService(db)

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
        return DashboardSummaryResponse(
            sync_status="synced",
            pending_sync_count=0,
            tasks_today=tasks_today,
            habits_today=habits_today,
            goals_progress=goals_progress,
            running_progress=running_progress,
            calendar_preview=[],
            notifications=[],
            recent_activity=[],
            quick_actions=[
                QuickActionItem(id="add_goal", label="New Goal", route="/goals/new", enabled=True),
                QuickActionItem(id="add_task", label="New Task", route="/tasks/new", enabled=True),
                QuickActionItem(id="add_habit", label="New Habit", route="/habits/new", enabled=True),
                QuickActionItem(id="log_run", label="Log Run", route="/running/new", enabled=True),
            ],
        )
