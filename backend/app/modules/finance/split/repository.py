from sqlalchemy import func, select
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
