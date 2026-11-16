"""Read-only, date-window queries over other modules' tables for the Timeline."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import Loan, LoanEMI
from app.modules.journal.models import JournalEntry
from app.modules.running.models import Run
from app.modules.tasks.models import Task
from app.modules.wishlist.models import WishlistItem


class TimelineRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def tasks_due(self, user_id: str, start: datetime, end: datetime) -> list[Task]:
        result = await self.db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.deleted_at.is_(None),
                Task.archived_at.is_(None),
                Task.due_date.is_not(None),
                Task.due_date >= start,
                Task.due_date < end,
            )
        )
        return list(result.scalars().all())

    async def runs(self, user_id: str, start: date, end: date) -> list[Run]:
        result = await self.db.execute(
            select(Run).where(Run.user_id == user_id, Run.run_date >= start, Run.run_date <= end)
        )
        return list(result.scalars().all())

    async def journal_entries(self, user_id: str, start: date, end: date) -> list[JournalEntry]:
        result = await self.db.execute(
            select(JournalEntry).where(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= start,
                JournalEntry.entry_date <= end,
            )
        )
        return list(result.scalars().all())

    async def loan_emis(self, user_id: str, start: date, end: date) -> list[tuple[LoanEMI, Loan]]:
        result = await self.db.execute(
            select(LoanEMI, Loan)
            .join(Loan, Loan.id == LoanEMI.loan_id)
            .where(Loan.user_id == user_id, LoanEMI.due_date >= start, LoanEMI.due_date <= end)
        )
        return [(emi, loan) for emi, loan in result.all()]

    async def wishlist_achieved(self, user_id: str, start: date, end: date) -> list[WishlistItem]:
        result = await self.db.execute(
            select(WishlistItem).where(
                WishlistItem.user_id == user_id,
                WishlistItem.achieved_date.is_not(None),
                WishlistItem.achieved_date >= start,
                WishlistItem.achieved_date <= end,
            )
        )
        return list(result.scalars().all())
