from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.finance.schemas import (
    BudgetCreate,
    BudgetResponse,
    FinanceSummary,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.modules.finance.service import FinanceService

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/summary", response_model=FinanceSummary)
async def finance_summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await FinanceService(db).summary(user.id)


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    txn_type: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).list_transactions(user.id, txn_type)


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).create_transaction(user.id, data)


@router.patch("/transactions/{txn_id}", response_model=TransactionResponse)
async def update_transaction(
    txn_id: str,
    data: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).update_transaction(user.id, txn_id, data)


@router.delete("/transactions/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    txn_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await FinanceService(db).delete_transaction(user.id, txn_id)


@router.get("/budgets", response_model=list[BudgetResponse])
async def list_budgets(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await FinanceService(db).list_budgets(user.id)


@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def upsert_budget(
    data: BudgetCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).upsert_budget(user.id, data)


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await FinanceService(db).delete_budget(user.id, budget_id)
