from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.modules.ai.provider import OpenAiProvider
from app.modules.career.models import CareerProject, JobApplication
from app.modules.coaches.schemas import COACH_TYPES, CoachChatResponse
from app.modules.communication.models import VocabularyWord
from app.modules.finance.models import FinanceBudget, FinanceTransaction
from app.modules.habits.models import Habit, HabitLog
from app.modules.learning.models import LearningItem
from app.modules.memory.repository import MemoryRepository
from app.modules.running.models import Run


class CoachesService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.provider = OpenAiProvider(self.settings)
        self.memory_repo = MemoryRepository(db)

    async def chat(self, user_id: str, coach_type: str, message: str) -> CoachChatResponse:
        if coach_type not in COACH_TYPES:
            from fastapi import HTTPException, status
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown coach type: {coach_type}")

        context, summary = await self._build_context(user_id, coach_type)
        memories = await self.memory_repo.list_items(user_id)
        memory_text = "\n".join(f"- {m.memory_key}: {m.memory_value}" for m in memories[:10])
        if memory_text:
            context = f"User memories:\n{memory_text}\n\n{context}"

        system = self._system_prompt(coach_type, context)
        if self.provider.enabled:
            try:
                reply = await self.provider.chat(system, message)
            except Exception as exc:
                reply = f"Coach context ready but AI provider failed: {exc}\n\nContext:\n{summary}"
        else:
            reply = (
                f"[{coach_type.title()} Coach — offline mode]\n"
                f"Set OPENAI_API_KEY for personalized coaching.\n\n"
                f"Based on your data:\n{summary}\n\n"
                f"You asked: {message}"
            )

        return CoachChatResponse(coach_type=coach_type, reply=reply, context_summary=summary)

    def _system_prompt(self, coach_type: str, context: str) -> str:
        roles = {
            "running": "You are a running coach. Focus on training load, recovery, consistency, and race readiness.",
            "career": "You are a career coach. Focus on projects, applications, skills, and professional growth.",
            "finance": "You are a finance coach. Focus on spending, budgets, savings, and financial habits.",
            "learning": "You are a learning coach. Focus on study plans, progress, and skill development.",
            "communication": "You are a communication coach. Focus on vocabulary, writing, and speaking practice.",
            "habits": "You are a habits coach. Focus on streaks, consistency, and sustainable routines.",
        }
        return (
            f"{roles[coach_type]} Use ONLY the personal context below. Be concise and actionable.\n\n"
            f"Personal context:\n{context}"
        )

    async def _build_context(self, user_id: str, coach_type: str) -> tuple[str, str]:
        since = date.today() - timedelta(days=30)
        lines: list[str] = []

        if coach_type == "running":
            runs = await self.db.execute(
                select(Run).where(Run.user_id == user_id).order_by(Run.run_date.desc()).limit(10)
            )
            for r in runs.scalars().all():
                lines.append(f"Run {r.run_date}: {r.distance_km}km, {r.duration_seconds // 60}min")
            total = await self.db.execute(
                select(func.coalesce(func.sum(Run.distance_km), 0)).where(
                    Run.user_id == user_id, Run.run_date >= since
                )
            )
            lines.append(f"30-day distance: {float(total.scalar() or 0):.1f} km")

        elif coach_type == "career":
            projects = await self.db.execute(
                select(CareerProject).where(CareerProject.user_id == user_id).limit(10)
            )
            for p in projects.scalars().all():
                lines.append(f"Project: {p.name}")
            apps = await self.db.execute(
                select(JobApplication).where(JobApplication.user_id == user_id).limit(5)
            )
            for a in apps.scalars().all():
                lines.append(f"Application: {a.company} — {a.role} ({a.status})")

        elif coach_type == "finance":
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
            lines.append(f"Total income: {float(income.scalar() or 0):.2f}")
            lines.append(f"Total expenses: {float(expense.scalar() or 0):.2f}")
            budgets = await self.db.execute(
                select(FinanceBudget).where(FinanceBudget.user_id == user_id)
            )
            for b in budgets.scalars().all():
                lines.append(f"Budget {b.category}: limit {b.monthly_limit}")

        elif coach_type == "learning":
            items = await self.db.execute(
                select(LearningItem).where(LearningItem.user_id == user_id).limit(10)
            )
            for l in items.scalars().all():
                lines.append(f"{l.item_type}: {l.title} — {l.status} ({l.progress}%)")

        elif coach_type == "communication":
            vocab = await self.db.execute(
                select(func.count()).select_from(VocabularyWord).where(VocabularyWord.user_id == user_id)
            )
            lines.append(f"Vocabulary items: {int(vocab.scalar() or 0)}")

        elif coach_type == "habits":
            habits = await self.db.execute(select(Habit).where(Habit.user_id == user_id))
            for h in habits.scalars().all():
                logs = await self.db.execute(
                    select(func.count())
                    .select_from(HabitLog)
                    .where(HabitLog.habit_id == h.id, HabitLog.log_date >= since)
                )
                lines.append(f"Habit {h.name}: {int(logs.scalar() or 0)} logs in 30d")

        context = "\n".join(lines) or "No records yet in this domain."
        summary = context[:500]
        return context, summary
