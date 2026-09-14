from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExpenseKind = Literal["soft", "hard"]
LoanStatus = Literal["ACTIVE", "CLOSED"]
EMIStatus = Literal["PENDING", "PAID", "CANCELLED"]


# --------------------------------------------------------------------------
# Expenses
# --------------------------------------------------------------------------

class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    amount: float = Field(gt=0)
    txn_date: date
    expense_kind: ExpenseKind
    category: str = "Other"
    notes: str | None = None


class ExpenseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    amount: float | None = Field(default=None, gt=0)
    txn_date: date | None = None
    expense_kind: ExpenseKind | None = None
    category: str | None = None
    notes: str | None = None


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    amount: float
    txn_date: date
    expense_kind: str | None
    category: str
    notes: str | None
    recurring_id: str | None
    loan_id: str | None
    loan_emi_id: str | None
    created_at: datetime


# --------------------------------------------------------------------------
# Income
# --------------------------------------------------------------------------

class IncomeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    amount: float = Field(gt=0)
    txn_date: date
    category: str = "Salary"
    is_recurring: bool = False
    notes: str | None = None


class IncomeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    amount: float | None = Field(default=None, gt=0)
    txn_date: date | None = None
    category: str | None = None
    is_recurring: bool | None = None
    notes: str | None = None


class IncomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None
    amount: float
    txn_date: date
    category: str
    is_recurring: bool
    notes: str | None
    created_at: datetime


# --------------------------------------------------------------------------
# Categories (user-extensible, backs the type-select component)
# --------------------------------------------------------------------------

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    txn_type: Literal["expense", "income"] = "expense"


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    txn_type: str


class CategoryOptions(BaseModel):
    expense: list[str]
    income: list[str]


# --------------------------------------------------------------------------
# Recurring definitions
# --------------------------------------------------------------------------

class RecurringCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    expense_kind: ExpenseKind = "hard"
    category: str = "Other"
    start_date: date
    end_date: date | None = None
    day_of_month: int = Field(default=1, ge=1, le=31)
    notes: str | None = None


class RecurringUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    amount: float | None = Field(default=None, gt=0)
    expense_kind: ExpenseKind | None = None
    category: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    is_active: bool | None = None
    notes: str | None = None


class RecurringResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    amount: float
    expense_kind: str
    category: str
    frequency: str
    start_date: date
    end_date: date | None
    day_of_month: int
    is_active: bool
    notes: str | None
    created_at: datetime


class GenerationResult(BaseModel):
    """What an idempotent generation pass actually created."""

    recurring_expenses_created: int
    emi_expenses_created: int


# --------------------------------------------------------------------------
# Loans and EMIs
# --------------------------------------------------------------------------

class LoanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    lender: str | None = Field(default=None, max_length=200)
    principal_amount: float = Field(gt=0)
    emi_amount: float = Field(gt=0)
    interest_rate: float | None = Field(default=None, ge=0)
    start_date: date
    emi_start_date: date
    tenure_months: int = Field(gt=0, le=600)
    emi_day: int = Field(default=1, ge=1, le=31)
    notes: str | None = None


class LoanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    lender: str | None = Field(default=None, max_length=200)
    principal_amount: float | None = Field(default=None, gt=0)
    emi_amount: float | None = Field(default=None, gt=0)
    interest_rate: float | None = Field(default=None, ge=0)
    notes: str | None = None
    status: LoanStatus | None = None


class LoanEMIResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    loan_id: str
    emi_number: int
    due_date: date
    amount: float
    status: str
    paid_date: date | None
    expense_id: str | None


class LoanResponse(BaseModel):
    """Loan with its progress figures derived from EMI rows.

    `emis_paid`, `emis_remaining` and `next_due_date` are computed on every read
    and are never stored — EMI records are the single source of truth.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    lender: str | None
    principal_amount: float
    emi_amount: float
    interest_rate: float | None
    start_date: date
    emi_start_date: date
    tenure_months: int
    emi_day: int
    status: str
    notes: str | None
    created_at: datetime

    # Derived
    emis_total: int = 0
    emis_paid: int = 0
    emis_remaining: int = 0
    next_due_date: date | None = None
    next_emi_amount: float | None = None


class LoanSummary(BaseModel):
    """Standing monthly obligation — not an extra expense figure."""

    active_loans: int
    monthly_emi_total: float


# --------------------------------------------------------------------------
# Overview / breakdown / upcoming
# --------------------------------------------------------------------------

class FinanceOverview(BaseModel):
    """Period totals.

    Deliberately carries no `net`, `remaining` or `savings` field: income is
    context, not a basis for judging what is left over.
    """

    period_start: date
    period_end: date
    label: str
    total_income: float
    total_expenses: float
    soft_expenses: float
    hard_expenses: float
    loan_emi_expenses: float
    recurring_expenses: float
    expense_count: int
    income_count: int


class CategoryTotal(BaseModel):
    category: str
    amount: float


class ExpenseBreakdown(BaseModel):
    period_start: date
    period_end: date
    categories: list[CategoryTotal]
    soft_total: float
    hard_total: float


class UpcomingItem(BaseModel):
    due_date: date
    title: str
    amount: float
    source: Literal["loan_emi", "recurring"]
    loan_id: str | None = None
    loan_emi_id: str | None = None
    recurring_id: str | None = None


# --------------------------------------------------------------------------
# Legacy contracts — preserved for the pre-existing transactions/budgets API
# and the modules that read them (coaches, predictions, automations).
# --------------------------------------------------------------------------

class TransactionCreate(BaseModel):
    txn_type: str
    amount: float = Field(gt=0)
    category: str = "other"
    description: str | None = None
    txn_date: date
    is_recurring: bool = False
    notes: str | None = None
    expense_kind: ExpenseKind | None = None


class TransactionUpdate(BaseModel):
    txn_type: str | None = None
    amount: float | None = Field(default=None, gt=0)
    category: str | None = None
    description: str | None = None
    txn_date: date | None = None
    is_recurring: bool | None = None
    notes: str | None = None
    expense_kind: ExpenseKind | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    txn_type: str
    amount: float
    category: str
    description: str | None
    txn_date: date
    is_recurring: bool
    notes: str | None
    expense_kind: str | None
    created_at: datetime


class BudgetCreate(BaseModel):
    category: str
    monthly_limit: float = Field(gt=0)


class BudgetUpdate(BaseModel):
    monthly_limit: float = Field(gt=0)


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    monthly_limit: float
    created_at: datetime


class FinanceSummary(BaseModel):
    """All-time totals. `net` was removed deliberately: the module reports
    recorded activity and obligations, never income minus expenses."""

    total_income: float
    total_expenses: float
    transaction_count: int
    budgets: list[BudgetResponse]
