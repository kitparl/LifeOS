from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.repository import FinanceRepository
from app.modules.finance.schemas import (
    BudgetCreate,
    BudgetResponse,
    FinanceSummary,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)


class FinanceService:
    def __init__(self, db: AsyncSession):
        self.repo = FinanceRepository(db)

    async def list_transactions(
        self, user_id: str, txn_type: str | None = None
    ) -> list[TransactionResponse]:
        txns = await self.repo.list_transactions(user_id, txn_type)
        return [TransactionResponse.model_validate(t) for t in txns]

    async def create_transaction(self, user_id: str, data: TransactionCreate) -> TransactionResponse:
        if data.txn_type not in ("income", "expense"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "txn_type must be income or expense")
        txn = await self.repo.create_transaction(user_id, data)
        return TransactionResponse.model_validate(txn)

    async def update_transaction(self, user_id: str, txn_id: str, data: TransactionUpdate) -> TransactionResponse:
        txn = await self.repo.get_transaction(user_id, txn_id)
        if not txn:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
        updated = await self.repo.update_transaction(txn, data)
        return TransactionResponse.model_validate(updated)

    async def delete_transaction(self, user_id: str, txn_id: str) -> None:
        txn = await self.repo.get_transaction(user_id, txn_id)
        if not txn:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
        await self.repo.delete_transaction(txn)

    async def list_budgets(self, user_id: str) -> list[BudgetResponse]:
        return [BudgetResponse.model_validate(b) for b in await self.repo.list_budgets(user_id)]

    async def upsert_budget(self, user_id: str, data: BudgetCreate) -> BudgetResponse:
        budget = await self.repo.upsert_budget(user_id, data)
        return BudgetResponse.model_validate(budget)

    async def delete_budget(self, user_id: str, budget_id: str) -> None:
        budget = await self.repo.delete_budget(user_id, budget_id)
        if not budget:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Budget not found")

    async def summary(self, user_id: str) -> FinanceSummary:
        txns = await self.repo.list_transactions(user_id)
        income = sum(t.amount for t in txns if t.txn_type == "income")
        expenses = sum(t.amount for t in txns if t.txn_type == "expense")
        budgets = await self.list_budgets(user_id)
        return FinanceSummary(
            total_income=income,
            total_expenses=expenses,
            net=income - expenses,
            transaction_count=len(txns),
            budgets=budgets,
        )
