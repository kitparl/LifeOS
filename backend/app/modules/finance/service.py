
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.finance.repository import FinanceRepository
from app.core.exceptions import BadRequestError, get_or_404
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
        self,
        user_id: str,
        txn_type: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[TransactionResponse], int]:
        txns, total = await self.repo.list_transactions(
            user_id, txn_type, limit=limit, offset=offset
        )
        return [TransactionResponse.model_validate(t) for t in txns], total

    async def create_transaction(self, user_id: str, data: TransactionCreate) -> TransactionResponse:
        if data.txn_type not in ("income", "expense"):
            raise BadRequestError("txn_type must be income or expense")
        txn = await self.repo.create_transaction(user_id, data)
        return TransactionResponse.model_validate(txn)

    async def update_transaction(self, user_id: str, txn_id: str, data: TransactionUpdate) -> TransactionResponse:
        txn = get_or_404(await self.repo.get_transaction(user_id, txn_id), "Transaction not found")
        updated = await self.repo.update_transaction(txn, data)
        return TransactionResponse.model_validate(updated)

    async def delete_transaction(self, user_id: str, txn_id: str) -> None:
        txn = get_or_404(await self.repo.get_transaction(user_id, txn_id), "Transaction not found")
        await self.repo.delete_transaction(txn)

    async def list_budgets(
        self, user_id: str, limit: int = 25, offset: int = 0
    ) -> tuple[list[BudgetResponse], int]:
        budgets, total = await self.repo.list_budgets(user_id, limit=limit, offset=offset)
        return [BudgetResponse.model_validate(b) for b in budgets], total

    async def upsert_budget(self, user_id: str, data: BudgetCreate) -> BudgetResponse:
        budget = await self.repo.upsert_budget(user_id, data)
        return BudgetResponse.model_validate(budget)

    async def delete_budget(self, user_id: str, budget_id: str) -> None:
        get_or_404(await self.repo.delete_budget(user_id, budget_id), "Budget not found")

    async def summary(self, user_id: str) -> FinanceSummary:
        txns, _ = await self.repo.list_transactions(user_id, limit=None)
        income = sum(t.amount for t in txns if t.txn_type == "income")
        expenses = sum(t.amount for t in txns if t.txn_type == "expense")
        budgets, _ = await self.list_budgets(user_id, limit=100)
        return FinanceSummary(
            total_income=income,
            total_expenses=expenses,
            net=income - expenses,
            transaction_count=len(txns),
            budgets=budgets,
        )
