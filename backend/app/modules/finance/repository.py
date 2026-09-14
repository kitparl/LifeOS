from datetime import date

from app.core.pagination import Pagination, paginate
from app.modules.finance.models import (
    FinanceBudget,
    FinanceCategory,
    FinanceRecurring,
    FinanceRecurringRun,
    FinanceTransaction,
    Loan,
    LoanEMI,
)
from app.modules.finance.schemas import BudgetCreate, TransactionCreate, TransactionUpdate
from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement


def _expense_sum(*conditions: ColumnElement[bool]) -> ColumnElement[float]:
    """SUM over expense rows matching extra conditions, 0 when empty."""
    predicate = FinanceTransaction.txn_type == "expense"
    for condition in conditions:
        predicate = predicate & condition
    return func.coalesce(func.sum(case((predicate, FinanceTransaction.amount), else_=0.0)), 0.0)


class FinanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Transactions (shared by the expense and income views)
    # ------------------------------------------------------------------

    async def list_transactions(
        self,
        user_id: str,
        txn_type: str | None = None,
        month: date | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[FinanceTransaction], int]:
        q = select(FinanceTransaction).where(FinanceTransaction.user_id == user_id)
        if txn_type:
            q = q.where(FinanceTransaction.txn_type == txn_type)
        if month:
            q = q.where(FinanceTransaction.txn_date >= month.replace(day=1))
        q = q.order_by(FinanceTransaction.txn_date.desc(), FinanceTransaction.created_at.desc())
        if limit is None:
            result = await self.db.execute(q)
            rows = list(result.scalars().all())
            return rows, len(rows)
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def list_in_period(
        self,
        user_id: str,
        txn_type: str,
        start: date,
        end: date,
        expense_kind: str | None = None,
        category: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[FinanceTransaction], int]:
        q = select(FinanceTransaction).where(
            FinanceTransaction.user_id == user_id,
            FinanceTransaction.txn_type == txn_type,
            FinanceTransaction.txn_date >= start,
            FinanceTransaction.txn_date <= end,
        )
        if expense_kind:
            q = q.where(FinanceTransaction.expense_kind == expense_kind)
        if category:
            q = q.where(FinanceTransaction.category == category)
        q = q.order_by(FinanceTransaction.txn_date.desc(), FinanceTransaction.created_at.desc())
        if limit is None:
            result = await self.db.execute(q)
            rows = list(result.scalars().all())
            return rows, len(rows)
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def get_transaction(self, user_id: str, txn_id: str) -> FinanceTransaction | None:
        result = await self.db.execute(
            select(FinanceTransaction).where(
                FinanceTransaction.id == txn_id, FinanceTransaction.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_transaction(self, user_id: str, data: TransactionCreate) -> FinanceTransaction:
        txn = FinanceTransaction(user_id=user_id, **data.model_dump())
        self.db.add(txn)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn

    async def add_transaction(self, txn: FinanceTransaction) -> FinanceTransaction:
        self.db.add(txn)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn

    async def update_transaction(
        self, txn: FinanceTransaction, data: TransactionUpdate
    ) -> FinanceTransaction:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(txn, key, value)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn

    async def apply_fields(self, txn: FinanceTransaction, fields: dict) -> FinanceTransaction:
        for key, value in fields.items():
            setattr(txn, key, value)
        await self.db.flush()
        await self.db.refresh(txn)
        return txn

    async def delete_transaction(self, txn: FinanceTransaction) -> None:
        await self.db.delete(txn)

    # ------------------------------------------------------------------
    # Period aggregates — computed in SQL, never by loading every row
    # ------------------------------------------------------------------

    async def period_totals(self, user_id: str, start: date, end: date) -> dict[str, float]:
        row = (
            await self.db.execute(
                select(
                    func.coalesce(
                        func.sum(
                            case(
                                (FinanceTransaction.txn_type == "income", FinanceTransaction.amount),
                                else_=0.0,
                            )
                        ),
                        0.0,
                    ).label("total_income"),
                    _expense_sum().label("total_expenses"),
                    _expense_sum(FinanceTransaction.expense_kind == "soft").label("soft_expenses"),
                    _expense_sum(FinanceTransaction.expense_kind == "hard").label("hard_expenses"),
                    _expense_sum(FinanceTransaction.loan_emi_id.is_not(None)).label("loan_emi_expenses"),
                    _expense_sum(FinanceTransaction.recurring_id.is_not(None)).label("recurring_expenses"),
                    func.count(case((FinanceTransaction.txn_type == "expense", 1))).label("expense_count"),
                    func.count(case((FinanceTransaction.txn_type == "income", 1))).label("income_count"),
                ).where(
                    FinanceTransaction.user_id == user_id,
                    FinanceTransaction.txn_date >= start,
                    FinanceTransaction.txn_date <= end,
                )
            )
        ).one()
        return {
            "total_income": float(row.total_income or 0),
            "total_expenses": float(row.total_expenses or 0),
            "soft_expenses": float(row.soft_expenses or 0),
            "hard_expenses": float(row.hard_expenses or 0),
            "loan_emi_expenses": float(row.loan_emi_expenses or 0),
            "recurring_expenses": float(row.recurring_expenses or 0),
            "expense_count": int(row.expense_count or 0),
            "income_count": int(row.income_count or 0),
        }

    async def category_totals(self, user_id: str, start: date, end: date) -> list[tuple[str, float]]:
        rows = await self.db.execute(
            select(FinanceTransaction.category, func.sum(FinanceTransaction.amount))
            .where(
                FinanceTransaction.user_id == user_id,
                FinanceTransaction.txn_type == "expense",
                FinanceTransaction.txn_date >= start,
                FinanceTransaction.txn_date <= end,
            )
            .group_by(FinanceTransaction.category)
            .order_by(func.sum(FinanceTransaction.amount).desc())
        )
        return [(row[0], float(row[1] or 0)) for row in rows.all()]

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    async def list_categories(self, user_id: str, txn_type: str | None = None) -> list[FinanceCategory]:
        q = select(FinanceCategory).where(FinanceCategory.user_id == user_id)
        if txn_type:
            q = q.where(FinanceCategory.txn_type == txn_type)
        result = await self.db.execute(q.order_by(FinanceCategory.name.asc()))
        return list(result.scalars().all())

    async def get_category(self, user_id: str, txn_type: str, name: str) -> FinanceCategory | None:
        result = await self.db.execute(
            select(FinanceCategory).where(
                FinanceCategory.user_id == user_id,
                FinanceCategory.txn_type == txn_type,
                FinanceCategory.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def create_category(self, user_id: str, txn_type: str, name: str) -> FinanceCategory:
        category = FinanceCategory(user_id=user_id, txn_type=txn_type, name=name)
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    # ------------------------------------------------------------------
    # Recurring definitions + generation ledger
    # ------------------------------------------------------------------

    async def list_recurring(
        self, user_id: str, active_only: bool = False
    ) -> list[FinanceRecurring]:
        q = select(FinanceRecurring).where(FinanceRecurring.user_id == user_id)
        if active_only:
            q = q.where(FinanceRecurring.is_active.is_(True))
        result = await self.db.execute(q.order_by(FinanceRecurring.day_of_month.asc()))
        return list(result.scalars().all())

    async def get_recurring(self, user_id: str, recurring_id: str) -> FinanceRecurring | None:
        result = await self.db.execute(
            select(FinanceRecurring).where(
                FinanceRecurring.id == recurring_id, FinanceRecurring.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def add_recurring(self, recurring: FinanceRecurring) -> FinanceRecurring:
        self.db.add(recurring)
        await self.db.flush()
        await self.db.refresh(recurring)
        return recurring

    async def delete_recurring(self, recurring: FinanceRecurring) -> None:
        await self.db.execute(
            delete(FinanceRecurringRun).where(FinanceRecurringRun.recurring_id == recurring.id)
        )
        await self.db.delete(recurring)

    async def claimed_periods(self, recurring_id: str) -> set[str]:
        """Months already generated for a definition — the idempotency check."""
        rows = await self.db.execute(
            select(FinanceRecurringRun.period).where(
                FinanceRecurringRun.recurring_id == recurring_id
            )
        )
        return {row[0] for row in rows.all()}

    async def record_run(self, recurring_id: str, period: str, expense_id: str | None) -> None:
        self.db.add(
            FinanceRecurringRun(recurring_id=recurring_id, period=period, expense_id=expense_id)
        )
        await self.db.flush()

    # ------------------------------------------------------------------
    # Loans
    # ------------------------------------------------------------------

    async def list_loans(self, user_id: str, status: str | None = None) -> list[Loan]:
        q = select(Loan).where(Loan.user_id == user_id)
        if status:
            q = q.where(Loan.status == status)
        result = await self.db.execute(q.order_by(Loan.created_at.desc()))
        return list(result.scalars().all())

    async def get_loan(self, user_id: str, loan_id: str) -> Loan | None:
        result = await self.db.execute(
            select(Loan).where(Loan.id == loan_id, Loan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add_loan(self, loan: Loan) -> Loan:
        self.db.add(loan)
        await self.db.flush()
        await self.db.refresh(loan)
        return loan

    # ------------------------------------------------------------------
    # Loan EMIs — the source of truth for loan progress
    # ------------------------------------------------------------------

    async def list_emis(self, loan_id: str) -> list[LoanEMI]:
        result = await self.db.execute(
            select(LoanEMI).where(LoanEMI.loan_id == loan_id).order_by(LoanEMI.emi_number.asc())
        )
        return list(result.scalars().all())

    async def get_emi_for_user(self, user_id: str, emi_id: str) -> LoanEMI | None:
        """Look an EMI up by its own id, scoped to the owning user."""
        result = await self.db.execute(
            select(LoanEMI).join(Loan, Loan.id == LoanEMI.loan_id).where(
                LoanEMI.id == emi_id, Loan.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_emi(self, loan_id: str, emi_id: str) -> LoanEMI | None:
        result = await self.db.execute(
            select(LoanEMI).where(LoanEMI.id == emi_id, LoanEMI.loan_id == loan_id)
        )
        return result.scalar_one_or_none()

    async def existing_emi_numbers(self, loan_id: str) -> set[int]:
        rows = await self.db.execute(select(LoanEMI.emi_number).where(LoanEMI.loan_id == loan_id))
        return {row[0] for row in rows.all()}

    async def add_emis(self, emis: list[LoanEMI]) -> None:
        if not emis:
            return
        self.db.add_all(emis)
        await self.db.flush()

    async def emi_counts(self, loan_id: str) -> dict[str, int]:
        rows = await self.db.execute(
            select(LoanEMI.status, func.count()).where(LoanEMI.loan_id == loan_id).group_by(LoanEMI.status)
        )
        counts = {status: int(count) for status, count in rows.all()}
        return {
            "total": sum(counts.values()),
            "paid": counts.get("PAID", 0),
            "pending": counts.get("PENDING", 0),
            "cancelled": counts.get("CANCELLED", 0),
        }

    async def next_pending_emi(self, loan_id: str) -> LoanEMI | None:
        result = await self.db.execute(
            select(LoanEMI)
            .where(LoanEMI.loan_id == loan_id, LoanEMI.status == "PENDING")
            .order_by(LoanEMI.due_date.asc(), LoanEMI.emi_number.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def due_emis_without_expense(self, user_id: str, through: date) -> list[tuple[LoanEMI, Loan]]:
        """EMIs whose due date has arrived but which have no expense row yet."""
        rows = await self.db.execute(
            select(LoanEMI, Loan)
            .join(Loan, Loan.id == LoanEMI.loan_id)
            .where(
                Loan.user_id == user_id,
                LoanEMI.due_date <= through,
                LoanEMI.expense_generated.is_(False),
                LoanEMI.status != "CANCELLED",
            )
            .order_by(LoanEMI.due_date.asc())
        )
        return [(emi, loan) for emi, loan in rows.all()]

    async def upcoming_emis(self, user_id: str, start: date, end: date) -> list[tuple[LoanEMI, Loan]]:
        rows = await self.db.execute(
            select(LoanEMI, Loan)
            .join(Loan, Loan.id == LoanEMI.loan_id)
            .where(
                Loan.user_id == user_id,
                Loan.status == "ACTIVE",
                LoanEMI.status == "PENDING",
                LoanEMI.due_date >= start,
                LoanEMI.due_date <= end,
            )
            .order_by(LoanEMI.due_date.asc())
        )
        return [(emi, loan) for emi, loan in rows.all()]

    async def monthly_emi_obligation(self, user_id: str) -> tuple[int, float]:
        row = (
            await self.db.execute(
                select(func.count(), func.coalesce(func.sum(Loan.emi_amount), 0.0)).where(
                    Loan.user_id == user_id, Loan.status == "ACTIVE"
                )
            )
        ).one()
        return int(row[0] or 0), float(row[1] or 0)

    # ------------------------------------------------------------------
    # Budgets — retained for Coaches / Predictions / Automations
    # ------------------------------------------------------------------

    async def list_budgets(
        self, user_id: str, limit: int | None = None, offset: int = 0
    ) -> tuple[list[FinanceBudget], int]:
        q = select(FinanceBudget).where(FinanceBudget.user_id == user_id)
        if limit is None:
            result = await self.db.execute(q)
            rows = list(result.scalars().all())
            return rows, len(rows)
        return await paginate(self.db, q, Pagination(limit=limit, offset=offset))

    async def upsert_budget(self, user_id: str, data: BudgetCreate) -> FinanceBudget:
        result = await self.db.execute(
            select(FinanceBudget).where(
                FinanceBudget.user_id == user_id, FinanceBudget.category == data.category
            )
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

    async def flush(self) -> None:
        """Persist pending ORM mutations so returned payloads reflect the write."""
        await self.db.flush()

    async def delete_budget(self, user_id: str, budget_id: str) -> FinanceBudget | None:
        result = await self.db.execute(
            select(FinanceBudget).where(
                FinanceBudget.id == budget_id, FinanceBudget.user_id == user_id
            )
        )
        budget = result.scalar_one_or_none()
        if budget:
            await self.db.delete(budget)
        return budget
