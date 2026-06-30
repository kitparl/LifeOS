from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    txn_type: str
    amount: float = Field(gt=0)
    category: str = "other"
    description: str | None = None
    txn_date: date
    is_recurring: bool = False
    notes: str | None = None


class TransactionUpdate(BaseModel):
    txn_type: str | None = None
    amount: float | None = Field(default=None, gt=0)
    category: str | None = None
    description: str | None = None
    txn_date: date | None = None
    is_recurring: bool | None = None
    notes: str | None = None


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
    total_income: float
    total_expenses: float
    net: float
    transaction_count: int
    budgets: list[BudgetResponse]
