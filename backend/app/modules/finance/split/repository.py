from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.split.models import (
    SplitExpense,
    SplitGroup,
    SplitHistory,
    SplitMember,
    SplitSettlement,
    SplitShare,
)


class SplitRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, *rows: object) -> None:
        self.db.add_all(rows)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Groups and seats
    # ------------------------------------------------------------------

    async def code_exists(self, code: str) -> bool:
        result = await self.db.execute(select(SplitGroup.id).where(SplitGroup.code == code))
        return result.scalar_one_or_none() is not None

    async def get_group_by_code(self, code: str) -> SplitGroup | None:
        result = await self.db.execute(select(SplitGroup).where(SplitGroup.code == code))
        return result.scalar_one_or_none()

    async def list_members(self, group_id: str) -> list[SplitMember]:
        result = await self.db.execute(
            select(SplitMember).where(SplitMember.group_id == group_id).order_by(SplitMember.seat_no)
        )
        return list(result.scalars().all())

    async def find_member_by_secret_hash(self, group_id: str, secret_hash: str) -> SplitMember | None:
        result = await self.db.execute(
            select(SplitMember).where(SplitMember.group_id == group_id, SplitMember.secret_hash == secret_hash)
        )
        return result.scalar_one_or_none()

    async def clear_upi(self, group_id: str) -> None:
        await self.db.execute(
            update(SplitMember)
            .where(SplitMember.group_id == group_id, SplitMember.upi_vpa.is_not(None))
            .values(upi_vpa=None)
        )

    async def clear_upi_of_closed_groups(self, now: datetime) -> int:
        closed = select(SplitGroup.id).where(or_(SplitGroup.ended_at.is_not(None), SplitGroup.expires_at <= now))
        result = await self.db.execute(
            update(SplitMember)
            .where(SplitMember.upi_vpa.is_not(None), SplitMember.group_id.in_(closed))
            .values(upi_vpa=None)
        )
        return result.rowcount or 0

    # ------------------------------------------------------------------
    # Ledger
    # ------------------------------------------------------------------

    async def list_expenses(self, group_id: str) -> list[SplitExpense]:
        result = await self.db.execute(
            select(SplitExpense)
            .where(SplitExpense.group_id == group_id)
            .order_by(SplitExpense.created_at, SplitExpense.id)
        )
        return list(result.scalars().all())

    async def list_shares(self, group_id: str) -> list[SplitShare]:
        result = await self.db.execute(
            select(SplitShare)
            .join(SplitExpense, SplitExpense.id == SplitShare.expense_id)
            .where(SplitExpense.group_id == group_id)
        )
        return list(result.scalars().all())

    async def list_settlements(self, group_id: str) -> list[SplitSettlement]:
        result = await self.db.execute(
            select(SplitSettlement)
            .where(SplitSettlement.group_id == group_id)
            .order_by(SplitSettlement.paid_at, SplitSettlement.id)
        )
        return list(result.scalars().all())

    async def get_settlement(self, settlement_id: str) -> SplitSettlement | None:
        return await self.db.get(SplitSettlement, settlement_id)

    async def get_group(self, group_id: str) -> SplitGroup | None:
        return await self.db.get(SplitGroup, group_id)

    async def count_expenses(self, group_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(SplitExpense).where(SplitExpense.group_id == group_id)
        )
        return int(result.scalar_one())

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    async def has_history(self, user_id: str, group_id: str) -> bool:
        result = await self.db.execute(
            select(SplitHistory.id).where(SplitHistory.user_id == user_id, SplitHistory.group_id == group_id)
        )
        return result.scalar_one_or_none() is not None

    async def list_history(self, user_id: str) -> list[tuple[SplitHistory, SplitGroup]]:
        result = await self.db.execute(
            select(SplitHistory, SplitGroup)
            .join(SplitGroup, SplitGroup.id == SplitHistory.group_id)
            .where(SplitHistory.user_id == user_id)
            .order_by(SplitHistory.created_at.desc())
        )
        return [(history, group) for history, group in result.all()]

    async def find_member_by_user(self, group_id: str, user_id: str) -> SplitMember | None:
        result = await self.db.execute(
            select(SplitMember)
            .where(SplitMember.group_id == group_id, SplitMember.user_id == user_id)
            .order_by(SplitMember.seat_no)
            .limit(1)
        )
        return result.scalar_one_or_none()
