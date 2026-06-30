from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.schemas import AnalyticsCharts, AnalyticsSummary, ChartPoint, ModuleCount
from app.modules.calendar.models import CalendarEvent
from app.modules.finance.models import FinanceTransaction
from app.modules.goals.models import Goal
from app.modules.habits.models import Habit, HabitLog
from app.modules.journal.models import JournalEntry
from app.modules.learning.models import LearningItem
from app.modules.qa.models import QAEntry
from app.modules.running.models import Run
from app.modules.tasks.models import Task


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def summary(self, user_id: str) -> AnalyticsSummary:
        since = datetime.now(UTC) - timedelta(days=30)
        since_date = date.today() - timedelta(days=30)

        async def count(model, user_col):
            result = await self.db.execute(select(func.count()).select_from(model).where(user_col == user_id))
            return int(result.scalar() or 0)

        modules = [
            ModuleCount(module="goals", count=await count(Goal, Goal.user_id)),
            ModuleCount(module="tasks", count=await count(Task, Task.user_id)),
            ModuleCount(module="habits", count=await count(Habit, Habit.user_id)),
            ModuleCount(module="runs", count=await count(Run, Run.user_id)),
            ModuleCount(module="journal", count=await count(JournalEntry, JournalEntry.user_id)),
            ModuleCount(module="learning", count=await count(LearningItem, LearningItem.user_id)),
            ModuleCount(module="qa", count=await count(QAEntry, QAEntry.user_id)),
            ModuleCount(module="calendar", count=await count(CalendarEvent, CalendarEvent.user_id)),
        ]

        tasks_done = await self.db.execute(
            select(func.count()).select_from(Task).where(Task.user_id == user_id, Task.status == "completed")
        )
        habits_30 = await self.db.execute(
            select(func.count())
            .select_from(HabitLog)
            .join(Habit, HabitLog.habit_id == Habit.id)
            .where(Habit.user_id == user_id, HabitLog.log_date >= since_date)
        )
        runs_30 = await self.db.execute(
            select(func.count()).select_from(Run).where(Run.user_id == user_id, Run.run_date >= since_date)
        )
        journal_30 = await self.db.execute(
            select(func.count()).select_from(JournalEntry).where(
                JournalEntry.user_id == user_id, JournalEntry.created_at >= since
            )
        )
        learning_prog = await self.db.execute(
            select(func.count()).select_from(LearningItem).where(
                LearningItem.user_id == user_id, LearningItem.status == "in_progress"
            )
        )
        income = await self.db.execute(
            select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                FinanceTransaction.user_id == user_id, FinanceTransaction.txn_type == "income"
            )
        )
        expense = await self.db.execute(
            select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                FinanceTransaction.user_id == user_id, FinanceTransaction.txn_type == "expense"
            )
        )
        net = float(income.scalar() or 0) - float(expense.scalar() or 0)

        return AnalyticsSummary(
            modules=modules,
            tasks_completed=int(tasks_done.scalar() or 0),
            habits_logged_30d=int(habits_30.scalar() or 0),
            runs_30d=int(runs_30.scalar() or 0),
            journal_entries_30d=int(journal_30.scalar() or 0),
            learning_in_progress=int(learning_prog.scalar() or 0),
            finance_net=net,
        )

    async def charts(self, user_id: str) -> AnalyticsCharts:
        task_rows = await self.db.execute(
            select(Task.status, func.count()).where(Task.user_id == user_id).group_by(Task.status)
        )
        tasks_by_status = [ChartPoint(label=row[0], value=float(row[1])) for row in task_rows.all()]

        exp_rows = await self.db.execute(
            select(FinanceTransaction.category, func.sum(FinanceTransaction.amount))
            .where(FinanceTransaction.user_id == user_id, FinanceTransaction.txn_type == "expense")
            .group_by(FinanceTransaction.category)
        )
        expenses = [ChartPoint(label=row[0], value=float(row[1] or 0)) for row in exp_rows.all()]

        learn_rows = await self.db.execute(
            select(LearningItem.item_type, func.count())
            .where(LearningItem.user_id == user_id)
            .group_by(LearningItem.item_type)
        )
        learning = [ChartPoint(label=row[0], value=float(row[1])) for row in learn_rows.all()]

        return AnalyticsCharts(
            tasks_by_status=tasks_by_status,
            expenses_by_category=expenses,
            learning_by_type=learning,
        )
