from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import ContentEmbedding
from app.modules.calendar.models import CalendarEvent
from app.modules.career.models import CareerProject, JobApplication
from app.modules.finance.models import FinanceTransaction
from app.modules.goals.models import Goal
from app.modules.habits.models import Habit
from app.modules.journal.models import JournalEntry
from app.modules.learning.models import LearningItem
from app.modules.qa.models import QAEntry
from app.modules.running.models import Run
from app.modules.tasks.models import Task
from app.modules.wishlist.models import WishlistItem


@dataclass
class IndexDocument:
    source_type: str
    source_id: str
    title: str
    content: str
    route: str


class AiIndexer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_documents(self, user_id: str) -> list[IndexDocument]:
        docs: list[IndexDocument] = []

        goals = await self.db.execute(select(Goal).where(Goal.user_id == user_id))
        for g in goals.scalars().all():
            text = " ".join(filter(None, [g.title, g.description, g.notes, g.category, g.status]))
            docs.append(IndexDocument("goal", g.id, g.title, text, f"/goals/{g.id}"))

        tasks = await self.db.execute(select(Task).where(Task.user_id == user_id))
        for t in tasks.scalars().all():
            text = " ".join(filter(None, [t.title, t.description, t.status, t.priority]))
            docs.append(IndexDocument("task", t.id, t.title, text, f"/tasks/{t.id}"))

        habits = await self.db.execute(select(Habit).where(Habit.user_id == user_id))
        for h in habits.scalars().all():
            text = " ".join(filter(None, [h.name, h.description, h.frequency]))
            docs.append(IndexDocument("habit", h.id, h.name, text, f"/habits/{h.id}"))

        runs = await self.db.execute(select(Run).where(Run.user_id == user_id))
        for r in runs.scalars().all():
            title = f"Run {r.distance_km}km"
            text = " ".join(filter(None, [title, r.notes, r.weather, str(r.run_date)]))
            docs.append(IndexDocument("run", r.id, title, text, f"/running/{r.id}"))

        events = await self.db.execute(select(CalendarEvent).where(CalendarEvent.user_id == user_id))
        for e in events.scalars().all():
            text = " ".join(filter(None, [e.title, e.description, e.location, e.category]))
            docs.append(IndexDocument("calendar", e.id, e.title, text, f"/calendar/{e.id}"))

        journals = await self.db.execute(select(JournalEntry).where(JournalEntry.user_id == user_id))
        for j in journals.scalars().all():
            text = " ".join(
                filter(None, [j.title, j.content, j.entry_type, j.gratitude, j.wins, j.lessons])
            )
            docs.append(IndexDocument("journal", j.id, j.title or "Journal", text, f"/journal/{j.id}"))

        qa_rows = await self.db.execute(select(QAEntry).where(QAEntry.user_id == user_id))
        for q in qa_rows.scalars().all():
            text = f"{q.question} {q.current_answer}"
            docs.append(IndexDocument("qa", q.id, q.question[:120], text, f"/qa/{q.id}"))

        wishes = await self.db.execute(select(WishlistItem).where(WishlistItem.user_id == user_id))
        for w in wishes.scalars().all():
            text = " ".join(filter(None, [w.title, w.description, w.notes, w.category]))
            docs.append(IndexDocument("wishlist", w.id, w.title, text, f"/wishlist/{w.id}"))

        learning = await self.db.execute(select(LearningItem).where(LearningItem.user_id == user_id))
        for l in learning.scalars().all():
            text = " ".join(filter(None, [l.title, l.provider, l.notes, l.item_type, l.status]))
            docs.append(IndexDocument("learning", l.id, l.title, text, f"/learning/{l.id}"))

        projects = await self.db.execute(select(CareerProject).where(CareerProject.user_id == user_id))
        for p in projects.scalars().all():
            text = " ".join(filter(None, [p.name, p.description, p.tech_stack]))
            docs.append(IndexDocument("career_project", p.id, p.name, text, "/career"))

        apps = await self.db.execute(select(JobApplication).where(JobApplication.user_id == user_id))
        for a in apps.scalars().all():
            title = f"{a.company} — {a.role}"
            text = " ".join(filter(None, [title, a.status, a.notes]))
            docs.append(IndexDocument("job_application", a.id, title, text, "/career"))

        txns = await self.db.execute(select(FinanceTransaction).where(FinanceTransaction.user_id == user_id))
        for t in txns.scalars().all():
            title = f"{t.txn_type} {t.amount}"
            text = " ".join(filter(None, [title, t.category, t.description, t.notes]))
            docs.append(IndexDocument("finance", t.id, title, text, "/finance"))

        return docs
