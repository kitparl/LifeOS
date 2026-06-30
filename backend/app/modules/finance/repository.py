from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.models import FinanceBudget, FinanceTransaction
from app.modules.finance.schemas import BudgetCreate, BudgetUpdate, TransactionCreate, TransactionUpdate


class FinanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_transactions(
        self, user_id: str, txn_type: str | None = None, month: date | None = None
    ) -> list[FinanceTransaction]:
        q = select(FinanceTransaction).where(FinanceTransaction.user_id == user_id)
        if txn_type:
            q = q.where(FinanceTransaction.txn_type == txn_type)
        if month:
            start = month.replace(day=1)
            q = q.where(FinanceTransaction.txn_date >= start)
        q = q.order_by(FinanceTransaction.txn_date.desc())
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_transaction(self, user_id: str, txn_id: str) -> FinanceTransaction | None:
        result = await self.db.execute(
            select(FinanceTransaction).where(FinanceTransaction.id == txn_id, FinanceTransaction.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_transaction(self, user_id: str, data: TransactionCreate) -> FinanceTransaction:
        txn = FinanceTransaction(user_id=user_id, **data.model_dump())
        self.db.add(txn)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn

    async def update_transaction(self, txn: FinanceTransaction, data: TransactionUpdate) -> FinanceTransaction:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(txn, key, value)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn

    async def delete_transaction(self, txn: FinanceTransaction) -> None:
        await self.db.delete(txn)

    async def list_budgets(self, user_id: str) -> list[FinanceBudget]:
        result = await self.db.execute(select(FinanceBudget).where(FinanceBudget.user_id == user_id))
        return list(result.scalars().all())

    async def upsert_budget(self, user_id: str, data: BudgetCreate) -> FinanceBudget:
        result = await self.db.execute(
            select(FinanceBudget).where(FinanceBudget.user_id == user_id, FinanceBudget.category == data.category)
        )
        budget = result.scalar_one_or_none()
        if budget:
            budget.monthly_limit = data.monthly_limit
        else:
            budget = FinanceBudget(user_id=user_id, **data.model_dump())
            self.db.add(budget)
        await self.db.flush()
        await self.db.refresh(budget)
        return budget

    async def delete_budget(self, user_id: str, budget_id: str) -> FinanceBudget | None:
        result = await self.db.execute(
            select(FinanceBudget).where(FinanceBudget.id == budget_id, FinanceBudget.user_id == user_id)
        )
        budget = result.scalar_one_or_none()
        if budget:
            await self.db.delete(budget)
        return budget
