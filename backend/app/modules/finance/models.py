import uuid
from datetime import UTC, date, datetime

from app.core.database import Base
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

TRANSACTION_TYPES = ("income", "expense")

# Soft = variable/lifestyle spend. Hard = fixed/committed obligation.
# The distinction exists to show expense burden and composition — it is not an
# accounting classification.
EXPENSE_KINDS = ("soft", "hard")

LOAN_STATUSES = ("ACTIVE", "COMPLETED", "FORECLOSED")
EMI_STATUSES = ("PENDING", "PAID", "CANCELLED")
PART_PAYMENT_IMPACTS = ("REDUCE_TENURE", "REDUCE_EMI")
RECURRING_FREQUENCIES = ("monthly",)

# Category reserved for loan EMI expenses. EMI expenses are always Hard.
LOAN_EMI_CATEGORY = "Loan EMI"

# Legacy tuple kept for the pre-existing transactions API and the modules that
# import it (coaches, predictions, automations).
FINANCE_CATEGORIES = (
    "salary", "freelance", "food", "rent", "transport", "utilities",
    "entertainment", "health", "education", "investment", "savings", "loan", "other",
)

DEFAULT_EXPENSE_CATEGORIES = (
    "Food", "Groceries", "Shopping", "Transport", "Rent", "Utilities",
    "Entertainment", "Health", "Education", "Insurance", "Subscriptions",
    LOAN_EMI_CATEGORY, "Other",
)

DEFAULT_INCOME_CATEGORIES = ("Salary", "Freelance", "Bonus", "Other Income")

# Substrings that mark a category as a fixed/committed obligation. Used once, to
# backfill expense_kind on rows that predate the Soft/Hard split.
# Deliberately avoids substrings that collide with Soft categories
# ("fee" matches coffee, "tax" matches taxi).
HARD_CATEGORY_HINTS = (
    "rent", "utilit", "electric", "water", "gas", "internet", "broadband",
    "loan", "emi", "mortgage", "insur", "health", "medical", "educat",
    "school", "tuition", "college", "subscription", "premium",
)


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class FinanceTransaction(Base):
    """A single recorded income or expense.

    `description` carries the user-facing title (e.g. "Zepto", "Electricity Bill").
    Expense rows additionally carry `expense_kind`, and — when they were produced
    by a recurring definition or a loan EMI — a link back to their origin.
    """

    __tablename__ = "finance_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    txn_type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    txn_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_recurring: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft/Hard classification — NULL on income rows.
    expense_kind: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    # Origin links: set when this row was generated rather than hand-entered.
    recurring_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    loan_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    loan_emi_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class FinanceBudget(Base):
    """Per-category monthly limit.

    Out of scope for the Finance UI (this is not a budgeting app), but retained
    because Coaches, Predictions and Automations read it.
    """

    __tablename__ = "finance_budgets"
    __table_args__ = (UniqueConstraint("user_id", "category", name="uq_finance_budget_category"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    monthly_limit: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class FinanceCategory(Base):
    """User-extensible category label, backing the `type-select` create flow.

    Mirrors the existing routine_areas / routine_categories precedent.
    """

    __tablename__ = "finance_categories"
    __table_args__ = (
        UniqueConstraint("user_id", "txn_type", "name", name="uq_finance_category_user_type_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    txn_type: Mapped[str] = mapped_column(String(16), nullable=False, default="expense")
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class FinanceRecurring(Base):
    """A monthly recurring expense definition.

    A definition is *not* an expense. It generates expenses, one per month, and
    those generated rows are what the totals count.
    """

    __tablename__ = "finance_recurring"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    txn_type: Mapped[str] = mapped_column(String(16), nullable=False, default="expense")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    expense_kind: Mapped[str] = mapped_column(String(8), nullable=False, default="hard")
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="Other")
    frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="monthly")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    day_of_month: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class FinanceRecurringRun(Base):
    """Ledger of which (definition, month) slots have already been generated.

    This is the idempotency guarantee: the unique constraint makes a second
    generation pass a no-op. It also means a generated expense the user deletes
    is never silently resurrected — the slot stays consumed.
    """

    __tablename__ = "finance_recurring_runs"
    __table_args__ = (
        UniqueConstraint("recurring_id", "period", name="uq_finance_recurring_run_period"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    recurring_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("finance_recurring.id", ondelete="CASCADE"), index=True, nullable=False
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # "YYYY-MM"
    expense_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Loan(Base):
    """A financial obligation with a principal, tenure, start date and eventual end.

    Deliberately independent of the expense system so a future Net Worth module
    can treat loans as liabilities without restructuring anything.

    Paid/remaining EMI counts and the next due date are NEVER stored here — they
    are derived from LoanEMI rows, which are the single source of truth.
    """

    __tablename__ = "finance_loans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    lender: Mapped[str | None] = mapped_column(String(200), nullable=True)
    principal_amount: Mapped[float] = mapped_column(Float, nullable=False)
    emi_amount: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    emi_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    emi_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Physical column stays `closed_at` (predates the Foreclosed rename) — no migration needed.
    foreclosed_at: Mapped[date | None] = mapped_column("closed_at", Date, nullable=True)
    foreclosure_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    foreclosure_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class LoanEMI(Base):
    """One instalment of a loan's schedule — the source of truth for loan progress.

    `expense_generated` (rather than `expense_id IS NOT NULL`) guards expense
    materialisation, so deleting a generated expense does not cause a duplicate
    on the next generation pass.
    """

    __tablename__ = "finance_loan_emis"
    __table_args__ = (
        UniqueConstraint("loan_id", "emi_number", name="uq_finance_loan_emi_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    loan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("finance_loans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    emi_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expense_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    expense_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class LoanPartPayment(Base):
    """A part-payment recorded against a loan — a tracking event, not a calculation.

    `resulting_emi_amount` / `resulting_tenure_months` record whichever value the
    user chose to track after this payment (mutually exclusive with `impact`).
    """

    __tablename__ = "finance_loan_part_payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    loan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("finance_loans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str] = mapped_column(String(16), nullable=False)
    resulting_emi_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    resulting_tenure_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
