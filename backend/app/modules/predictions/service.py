from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import FinanceBudget, FinanceTransaction
from app.modules.goals.models import Goal
from app.modules.habits.models import Habit, HabitLog
from app.modules.journal.models import JournalEntry
from app.modules.learning.models import LearningItem
from app.modules.predictions.schemas import PredictionItem, PredictionsSummary
from app.modules.running.models import Run
from app.modules.tasks.models import Task


def _level(score: float) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


class PredictionsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def summary(self, user_id: str) -> PredictionsSummary:
        since = date.today() - timedelta(days=14)
        since_dt = datetime.now(UTC) - timedelta(days=14)

        runs = await self.db.execute(
            select(func.coalesce(func.sum(Run.distance_km), 0), func.count()).where(
                Run.user_id == user_id, Run.run_date >= since
            )
        )
        run_row = runs.one()
        weekly_km = float(run_row[0] or 0) / 2
        run_count = int(run_row[1] or 0)
        readiness = min(100.0, weekly_km * 2.5 + run_count * 5)

        journal = await self.db.execute(
            select(func.count()).select_from(JournalEntry).where(
                JournalEntry.user_id == user_id, JournalEntry.created_at >= since_dt
            )
        )
        habits = await self.db.execute(
            select(func.count())
            .select_from(HabitLog)
            .join(Habit, HabitLog.habit_id == Habit.id)
            .where(Habit.user_id == user_id, HabitLog.log_date >= since)
        )
        tasks_open = await self.db.execute(
            select(func.count()).select_from(Task).where(
                Task.user_id == user_id, Task.status != "completed"
            )
        )
        j_count = int(journal.scalar() or 0)
        h_count = int(habits.scalar() or 0)
        t_open = int(tasks_open.scalar() or 0)
        burnout = min(100.0, max(0.0, t_open * 3 + (14 - j_count) * 4 - h_count * 2))

        month_start = date.today().replace(day=1)
        spent = await self.db.execute(
            select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                FinanceTransaction.user_id == user_id,
                FinanceTransaction.txn_type == "expense",
                FinanceTransaction.txn_date >= month_start,
            )
        )
        budget_sum = await self.db.execute(
            select(func.coalesce(func.sum(FinanceBudget.monthly_limit), 0)).where(
                FinanceBudget.user_id == user_id
            )
        )
        total_spent = float(spent.scalar() or 0)
        total_budget = float(budget_sum.scalar() or 1)
        spend_ratio = total_spent / total_budget if total_budget > 0 else 0
        overspend = min(100.0, spend_ratio * 100)

        learning = await self.db.execute(
            select(func.count()).select_from(LearningItem).where(
                LearningItem.user_id == user_id, LearningItem.status == "in_progress"
            )
        )
        learning_done = await self.db.execute(
            select(func.count()).select_from(LearningItem).where(
                LearningItem.user_id == user_id, LearningItem.status == "completed"
            )
        )
        in_prog = int(learning.scalar() or 0)
        done = int(learning_done.scalar() or 0)
        learning_score = min(100.0, done * 10 + in_prog * 5 + h_count)

        goals_total = await self.db.execute(
            select(func.count()).select_from(Goal).where(Goal.user_id == user_id)
        )
        goals_done = await self.db.execute(
            select(func.count()).select_from(Goal).where(Goal.user_id == user_id, Goal.status == "completed")
        )
        gt = int(goals_total.scalar() or 0)
        gd = int(goals_done.scalar() or 0)
        goal_prob = (gd / gt * 100) if gt > 0 else 50.0
        goal_prob = min(100.0, goal_prob + readiness * 0.2 - burnout * 0.15)

        return PredictionsSummary(
            running_readiness=PredictionItem(
                key="running_readiness",
                label="Running Readiness",
                score=round(readiness, 1),
                level=_level(readiness),
                summary=f"~{weekly_km:.1f} km/week over last 2 weeks ({run_count} runs)",
            ),
            burnout_risk=PredictionItem(
                key="burnout_risk",
                label="Burnout Risk",
                score=round(burnout, 1),
                level=_level(burnout),
                summary=f"{j_count} journal entries, {t_open} open tasks in 14 days",
            ),
            overspending_risk=PredictionItem(
                key="overspending_risk",
                label="Overspending Risk",
                score=round(overspend, 1),
                level=_level(overspend),
                summary=f"Spent {total_spent:.0f} vs budget {total_budget:.0f} this month",
            ),
            learning_consistency=PredictionItem(
                key="learning_consistency",
                label="Learning Consistency",
                score=round(learning_score, 1),
                level=_level(learning_score),
                summary=f"{in_prog} in progress, {done} completed",
            ),
            goal_completion_probability=PredictionItem(
                key="goal_completion_probability",
                label="Goal Completion Probability",
                score=round(goal_prob, 1),
                level=_level(goal_prob),
                summary=f"{gd}/{gt} goals completed" if gt else "No goals yet",
            ),
        )
