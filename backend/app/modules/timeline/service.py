from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.models import CalendarEvent
from app.modules.finance.models import FinanceTransaction
from app.modules.goals.models import Goal
from app.modules.habits.models import HabitLog, Habit
from app.modules.journal.models import JournalEntry
from app.modules.learning.models import LearningItem
from app.modules.qa.models import QAEntry
from app.modules.running.models import Run
from app.modules.tasks.models import Task
from app.modules.timeline.schemas import TimelineItem


class TimelineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_events(self, user_id: str, limit: int = 100) -> list[TimelineItem]:
        items: list[TimelineItem] = []

        goals = await self.db.execute(select(Goal).where(Goal.user_id == user_id))
        for g in goals.scalars().all():
            items.append(
                TimelineItem(
                    module="goals", entity_type="goal", id=g.id, title=g.title,
                    occurred_at=g.updated_at, route=f"/goals/{g.id}",
                )
            )

        tasks = await self.db.execute(select(Task).where(Task.user_id == user_id))
        for t in tasks.scalars().all():
            at = t.completed_at or t.updated_at
            items.append(
                TimelineItem(
                    module="tasks", entity_type="task", id=t.id, title=t.title,
                    occurred_at=at, route=f"/tasks/{t.id}",
                )
            )

        runs = await self.db.execute(select(Run).where(Run.user_id == user_id))
        for r in runs.scalars().all():
            at = datetime.combine(r.run_date, datetime.min.time()).replace(tzinfo=r.created_at.tzinfo)
            items.append(
                TimelineItem(
                    module="running", entity_type="run", id=r.id,
                    title=f"Run {r.distance_km}km", occurred_at=at, route=f"/running/{r.id}",
                )
            )

        journals = await self.db.execute(select(JournalEntry).where(JournalEntry.user_id == user_id))
        for j in journals.scalars().all():
            at = datetime.combine(j.entry_date, datetime.min.time()).replace(tzinfo=j.created_at.tzinfo)
            items.append(
                TimelineItem(
                    module="journal", entity_type="journal", id=j.id,
                    title=j.title or "Journal", occurred_at=at, route=f"/journal/{j.id}",
                )
            )

        events = await self.db.execute(select(CalendarEvent).where(CalendarEvent.user_id == user_id))
        for e in events.scalars().all():
            items.append(
                TimelineItem(
                    module="calendar", entity_type="event", id=e.id, title=e.title,
                    occurred_at=e.starts_at, route=f"/calendar/{e.id}",
                )
            )

        txns = await self.db.execute(select(FinanceTransaction).where(FinanceTransaction.user_id == user_id))
        for t in txns.scalars().all():
            at = datetime.combine(t.txn_date, datetime.min.time()).replace(tzinfo=t.created_at.tzinfo)
            items.append(
                TimelineItem(
                    module="finance", entity_type="transaction", id=t.id,
                    title=f"{t.txn_type}: {t.amount}", occurred_at=at, route="/finance",
                )
            )

        learning = await self.db.execute(select(LearningItem).where(LearningItem.user_id == user_id))
        for l in learning.scalars().all():
            items.append(
                TimelineItem(
                    module="learning", entity_type="learning", id=l.id, title=l.title,
                    occurred_at=l.updated_at, route=f"/learning/{l.id}",
                )
            )

        qa = await self.db.execute(select(QAEntry).where(QAEntry.user_id == user_id))
        for q in qa.scalars().all():
            items.append(
                TimelineItem(
                    module="qa", entity_type="qa", id=q.id, title=q.question[:80],
                    occurred_at=q.updated_at, route=f"/qa/{q.id}",
                )
            )

        items.sort(key=lambda x: x.occurred_at, reverse=True)
        return items[:limit]
