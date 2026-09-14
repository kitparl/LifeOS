from datetime import date

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.finance.schemas import (
    BudgetCreate,
    BudgetResponse,
    CategoryCreate,
    CategoryOptions,
    ExpenseBreakdown,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    FinanceOverview,
    FinanceSummary,
    GenerationResult,
    IncomeCreate,
    IncomeResponse,
    IncomeUpdate,
    LoanCreate,
    LoanEMIResponse,
    LoanForecloseRequest,
    LoanPartPaymentCreate,
    LoanPartPaymentResponse,
    LoanResponse,
    LoanSummary,
    LoanUpdate,
    RecurringCreate,
    RecurringResponse,
    RecurringUpdate,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    UpcomingItem,
)
from app.modules.finance.service import FinanceService
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/finance", tags=["finance"])

# Shared period filter. Defaults to the current calendar month and stays there
# even when that month has no activity.
PeriodPreset = Query(default="this_month", pattern="^(this_month|last_month|this_year|custom)$")


# ----------------------------------------------------------------------
# Overview
# ----------------------------------------------------------------------

@router.get("/overview", response_model=FinanceOverview)
async def finance_overview(
    preset: str = PeriodPreset,
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).overview(user.id, preset, start, end)


@router.get("/breakdown", response_model=ExpenseBreakdown)
async def expense_breakdown(
    preset: str = PeriodPreset,
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).breakdown(user.id, preset, start, end)


@router.get("/upcoming", response_model=list[UpcomingItem])
async def upcoming_payments(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).upcoming(user.id, days)


# ----------------------------------------------------------------------
# Expenses
# ----------------------------------------------------------------------

@router.get("/expenses", response_model=list[ExpenseResponse])
async def list_expenses(
    response: Response,
    preset: str = PeriodPreset,
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    expense_kind: str | None = Query(default=None, pattern="^(soft|hard)$"),
    category: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await FinanceService(db).list_expenses(
        user.id, preset, start, end, expense_kind, category, limit=limit, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    data: ExpenseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).create_expense(user.id, data)


@router.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: str,
    data: ExpenseUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).update_expense(user.id, expense_id, data)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await FinanceService(db).delete_expense(user.id, expense_id)


# ----------------------------------------------------------------------
# Income
# ----------------------------------------------------------------------

@router.get("/income", response_model=list[IncomeResponse])
async def list_income(
    response: Response,
    preset: str = PeriodPreset,
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await FinanceService(db).list_income(
        user.id, preset, start, end, limit=limit, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/income", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
async def create_income(
    data: IncomeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).create_income(user.id, data)


@router.patch("/income/{income_id}", response_model=IncomeResponse)
async def update_income(
    income_id: str,
    data: IncomeUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).update_income(user.id, income_id, data)


@router.delete("/income/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income(
    income_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await FinanceService(db).delete_income(user.id, income_id)


# ----------------------------------------------------------------------
# Categories (backs the type-select component)
# ----------------------------------------------------------------------

@router.get("/categories", response_model=CategoryOptions)
async def list_categories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).category_options(user.id)


@router.post("/categories", response_model=CategoryOptions, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).create_category(user.id, data.txn_type, data.name)


# ----------------------------------------------------------------------
# Recurring definitions
# ----------------------------------------------------------------------

@router.get("/recurring", response_model=list[RecurringResponse])
async def list_recurring(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).list_recurring(user.id)


@router.post("/recurring", response_model=RecurringResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring(
    data: RecurringCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).create_recurring(user.id, data)


@router.patch("/recurring/{recurring_id}", response_model=RecurringResponse)
async def update_recurring(
    recurring_id: str,
    data: RecurringUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).update_recurring(user.id, recurring_id, data)


@router.delete("/recurring/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring(
    recurring_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await FinanceService(db).delete_recurring(user.id, recurring_id)


@router.post("/recurring/generate", response_model=GenerationResult)
async def generate_due(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run the idempotent generation pass explicitly. Safe to call repeatedly."""
    return await FinanceService(db).run_generation(user.id)


# ----------------------------------------------------------------------
# Loans
# ----------------------------------------------------------------------

@router.get("/loans", response_model=list[LoanResponse])
async def list_loans(
    loan_status: str | None = Query(default=None, pattern="^(ACTIVE|COMPLETED|FORECLOSED)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).list_loans(user.id, loan_status)


@router.get("/loans/summary", response_model=LoanSummary)
async def loans_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).loan_summary(user.id)


@router.post("/loans", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def create_loan(
    data: LoanCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).create_loan(user.id, data)


@router.get("/loans/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).get_loan(user.id, loan_id)


@router.patch("/loans/{loan_id}", response_model=LoanResponse)
async def update_loan(
    loan_id: str,
    data: LoanUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).update_loan(user.id, loan_id, data)


@router.delete("/loans/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loan(
    loan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await FinanceService(db).delete_loan(user.id, loan_id)


@router.post("/loans/{loan_id}/foreclose", response_model=LoanResponse)
async def foreclose_loan(
    loan_id: str,
    data: LoanForecloseRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).foreclose_loan(user.id, loan_id, data)


@router.post("/loans/{loan_id}/reactivate", response_model=LoanResponse)
async def reactivate_loan(
    loan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).reactivate_loan(user.id, loan_id)


@router.get("/loans/{loan_id}/part-payments", response_model=list[LoanPartPaymentResponse])
async def list_loan_part_payments(
    loan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).list_part_payments(user.id, loan_id)


@router.post(
    "/loans/{loan_id}/part-payments",
    response_model=LoanPartPaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_loan_part_payment(
    loan_id: str,
    data: LoanPartPaymentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).add_part_payment(user.id, loan_id, data)


@router.get("/loans/{loan_id}/emis", response_model=list[LoanEMIResponse])
async def list_loan_emis(
    loan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).list_emis(user.id, loan_id)


@router.post("/loans/{loan_id}/emis/{emi_id}/pay", response_model=LoanEMIResponse)
async def pay_loan_emi(
    loan_id: str,
    emi_id: str,
    paid_date: date | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService(db).mark_emi_paid(user.id, loan_id, emi_id, paid_date)


# ----------------------------------------------------------------------
# Legacy endpoints — kept for existing consumers
# ----------------------------------------------------------------------

@router.get("/summary", response_model=FinanceSummary)
async def finance_summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await FinanceService(db).summary(user.id)


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    response: Response,
    txn_type: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await FinanceService(db).list_transactions(
        user.id, txn_type, limit=limit, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return items


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
async def list_budgets(
    response: Response,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await FinanceService(db).list_budgets(user.id, limit=limit, offset=offset)
    response.headers["X-Total-Count"] = str(total)
    return items


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
