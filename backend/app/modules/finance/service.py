"""Finance business logic.

Two rules shape this module:

1. **Loan is not a recurring expense.** A Loan is an obligation; it produces
   LoanEMI rows; an EMI, once due, produces an Expense. Nothing collapses those
   three into one.
2. **Nothing is ever counted twice, and history is never rewritten.** Generation
   is idempotent, and edits to definitions affect only what has not happened yet.
"""

from datetime import date

from app.core.exceptions import BadRequestError, get_or_404
from app.modules.finance.generation import (
    emi_schedule,
    period_bounds,
    period_key,
    recurring_due_dates,
)
from app.modules.finance.models import (
    DEFAULT_EXPENSE_CATEGORIES,
    DEFAULT_INCOME_CATEGORIES,
    LOAN_EMI_CATEGORY,
    FinanceRecurring,
    FinanceTransaction,
    Loan,
    LoanEMI,
)
from app.modules.finance.repository import FinanceRepository
from app.modules.finance.schemas import (
    BudgetCreate,
    BudgetResponse,
    CategoryOptions,
    CategoryTotal,
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
from sqlalchemy.ext.asyncio import AsyncSession

_MONTH_LABELS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


def _period_label(start: date, end: date) -> str:
    """Human label for a range: 'September 2026', '2026', or an explicit span."""
    if start.year == end.year:
        if start.month == end.month:
            return f"{_MONTH_LABELS[start.month - 1]} {start.year}"
        if (start.month, start.day) == (1, 1) and (end.month, end.day) == (12, 31):
            return str(start.year)
    return f"{start.isoformat()} — {end.isoformat()}"


def _expense_response(txn: FinanceTransaction) -> ExpenseResponse:
    return ExpenseResponse(
        id=txn.id,
        title=txn.description,
        amount=txn.amount,
        txn_date=txn.txn_date,
        expense_kind=txn.expense_kind,
        category=txn.category,
        notes=txn.notes,
        recurring_id=txn.recurring_id,
        loan_id=txn.loan_id,
        loan_emi_id=txn.loan_emi_id,
        created_at=txn.created_at,
    )


def _income_response(txn: FinanceTransaction) -> IncomeResponse:
    return IncomeResponse(
        id=txn.id,
        title=txn.description,
        amount=txn.amount,
        txn_date=txn.txn_date,
        category=txn.category,
        is_recurring=txn.is_recurring,
        notes=txn.notes,
        created_at=txn.created_at,
    )


class FinanceService:
    def __init__(self, db: AsyncSession):
        self.repo = FinanceRepository(db)

    @staticmethod
    def _today() -> date:
        return date.today()

    # ==================================================================
    # Generation — idempotent, safe to run on every read
    # ==================================================================

    async def run_generation(self, user_id: str, through: date | None = None) -> GenerationResult:
        through = through or self._today()
        recurring_created = await self._generate_recurring(user_id, through)
        emi_created = await self._generate_emi_expenses(user_id, through)
        return GenerationResult(
            recurring_expenses_created=recurring_created,
            emi_expenses_created=emi_created,
        )

    async def _generate_recurring(self, user_id: str, through: date) -> int:
        created = 0
        for definition in await self.repo.list_recurring(user_id, active_only=True):
            claimed = await self.repo.claimed_periods(definition.id)
            due_dates = recurring_due_dates(
                definition.start_date, definition.end_date, definition.day_of_month, through
            )
            for due in due_dates:
                slot = period_key(due)
                if slot in claimed:
                    continue
                expense = await self.repo.add_transaction(
                    FinanceTransaction(
                        user_id=user_id,
                        txn_type="expense",
                        amount=definition.amount,
                        category=definition.category,
                        description=definition.title,
                        txn_date=due,
                        is_recurring=True,
                        notes=definition.notes,
                        expense_kind=definition.expense_kind,
                        recurring_id=definition.id,
                    )
                )
                await self.repo.record_run(definition.id, slot, expense.id)
                claimed.add(slot)
                created += 1
        return created

    async def _generate_emi_expenses(self, user_id: str, through: date) -> int:
        created = 0
        for emi, loan in await self.repo.due_emis_without_expense(user_id, through):
            await self._materialise_emi_expense(user_id, emi, loan)
            created += 1
        return created

    async def _materialise_emi_expense(self, user_id: str, emi: LoanEMI, loan: Loan) -> None:
        """Create the Hard Expense behind an EMI — exactly once.

        `expense_generated` is the guard rather than `expense_id`, so deleting
        the expense later does not cause a duplicate on the next pass.
        """
        if emi.expense_generated:
            return
        expense = await self.repo.add_transaction(
            FinanceTransaction(
                user_id=user_id,
                txn_type="expense",
                amount=emi.amount,
                category=LOAN_EMI_CATEGORY,
                description=f"{loan.name} EMI {emi.emi_number}",
                txn_date=emi.due_date,
                is_recurring=False,
                expense_kind="hard",
                loan_id=loan.id,
                loan_emi_id=emi.id,
            )
        )
        emi.expense_id = expense.id
        emi.expense_generated = True
        await self.repo.flush()

    # ==================================================================
    # Overview / breakdown / upcoming
    # ==================================================================

    async def overview(
        self,
        user_id: str,
        preset: str = "this_month",
        start: date | None = None,
        end: date | None = None,
    ) -> FinanceOverview:
        period_start, period_end = period_bounds(preset, self._today(), start, end)
        await self.run_generation(user_id)
        totals = await self.repo.period_totals(user_id, period_start, period_end)
        return FinanceOverview(
            period_start=period_start,
            period_end=period_end,
            label=_period_label(period_start, period_end),
            **totals,
        )

    async def breakdown(
        self,
        user_id: str,
        preset: str = "this_month",
        start: date | None = None,
        end: date | None = None,
    ) -> ExpenseBreakdown:
        period_start, period_end = period_bounds(preset, self._today(), start, end)
        await self.run_generation(user_id)
        rows = await self.repo.category_totals(user_id, period_start, period_end)
        totals = await self.repo.period_totals(user_id, period_start, period_end)
        return ExpenseBreakdown(
            period_start=period_start,
            period_end=period_end,
            categories=[CategoryTotal(category=name, amount=amount) for name, amount in rows],
            soft_total=totals["soft_expenses"],
            hard_total=totals["hard_expenses"],
        )

    async def upcoming(self, user_id: str, days: int = 30) -> list[UpcomingItem]:
        """Pending EMIs and not-yet-generated recurring expenses in the window."""
        today = self._today()
        horizon = date.fromordinal(today.toordinal() + max(days, 1))
        items: list[UpcomingItem] = []

        for emi, loan in await self.repo.upcoming_emis(user_id, today, horizon):
            items.append(
                UpcomingItem(
                    due_date=emi.due_date,
                    title=f"{loan.name} EMI",
                    amount=emi.amount,
                    source="loan_emi",
                    loan_id=loan.id,
                    loan_emi_id=emi.id,
                )
            )

        for definition in await self.repo.list_recurring(user_id, active_only=True):
            claimed = await self.repo.claimed_periods(definition.id)
            for due in recurring_due_dates(
                definition.start_date, definition.end_date, definition.day_of_month, horizon
            ):
                if due < today or period_key(due) in claimed:
                    continue
                items.append(
                    UpcomingItem(
                        due_date=due,
                        title=definition.title,
                        amount=definition.amount,
                        source="recurring",
                        recurring_id=definition.id,
                    )
                )

        return sorted(items, key=lambda item: (item.due_date, item.title))

    # ==================================================================
    # Expenses
    # ==================================================================

    async def list_expenses(
        self,
        user_id: str,
        preset: str = "this_month",
        start: date | None = None,
        end: date | None = None,
        expense_kind: str | None = None,
        category: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[ExpenseResponse], int]:
        period_start, period_end = period_bounds(preset, self._today(), start, end)
        await self.run_generation(user_id)
        rows, total = await self.repo.list_in_period(
            user_id,
            "expense",
            period_start,
            period_end,
            expense_kind=expense_kind,
            category=category,
            limit=limit,
            offset=offset,
        )
        return [_expense_response(row) for row in rows], total

    async def create_expense(self, user_id: str, data: ExpenseCreate) -> ExpenseResponse:
        await self._remember_category(user_id, "expense", data.category)
        txn = await self.repo.add_transaction(
            FinanceTransaction(
                user_id=user_id,
                txn_type="expense",
                amount=data.amount,
                category=data.category,
                description=data.title,
                txn_date=data.txn_date,
                notes=data.notes,
                expense_kind=data.expense_kind,
            )
        )
        return _expense_response(txn)

    async def update_expense(
        self, user_id: str, expense_id: str, data: ExpenseUpdate
    ) -> ExpenseResponse:
        txn = get_or_404(await self.repo.get_transaction(user_id, expense_id), "Expense not found")
        if txn.txn_type != "expense":
            raise BadRequestError("Not an expense")

        fields = data.model_dump(exclude_unset=True)
        if "title" in fields:
            fields["description"] = fields.pop("title")
        # A loan EMI is a committed obligation — it stays Hard whatever the edit says.
        if txn.loan_emi_id and fields.get("expense_kind") == "soft":
            raise BadRequestError("Loan EMI expenses are always Hard expenses")
        if "category" in fields:
            await self._remember_category(user_id, "expense", fields["category"])

        return _expense_response(await self.repo.apply_fields(txn, fields))

    async def delete_expense(self, user_id: str, expense_id: str) -> None:
        txn = get_or_404(await self.repo.get_transaction(user_id, expense_id), "Expense not found")
        # Unlink the origin but leave its generation marker intact, so a deleted
        # generated expense is never silently recreated on the next pass.
        if txn.loan_emi_id:
            emi = await self.repo.get_emi_for_user(user_id, txn.loan_emi_id)
            if emi:
                emi.expense_id = None
        await self.repo.delete_transaction(txn)
        await self.repo.flush()

    # ==================================================================
    # Income
    # ==================================================================

    async def list_income(
        self,
        user_id: str,
        preset: str = "this_month",
        start: date | None = None,
        end: date | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[IncomeResponse], int]:
        period_start, period_end = period_bounds(preset, self._today(), start, end)
        rows, total = await self.repo.list_in_period(
            user_id, "income", period_start, period_end, limit=limit, offset=offset
        )
        return [_income_response(row) for row in rows], total

    async def create_income(self, user_id: str, data: IncomeCreate) -> IncomeResponse:
        await self._remember_category(user_id, "income", data.category)
        txn = await self.repo.add_transaction(
            FinanceTransaction(
                user_id=user_id,
                txn_type="income",
                amount=data.amount,
                category=data.category,
                description=data.title,
                txn_date=data.txn_date,
                is_recurring=data.is_recurring,
                notes=data.notes,
            )
        )
        return _income_response(txn)

    async def update_income(
        self, user_id: str, income_id: str, data: IncomeUpdate
    ) -> IncomeResponse:
        txn = get_or_404(await self.repo.get_transaction(user_id, income_id), "Income not found")
        if txn.txn_type != "income":
            raise BadRequestError("Not an income record")
        fields = data.model_dump(exclude_unset=True)
        if "title" in fields:
            fields["description"] = fields.pop("title")
        if "category" in fields:
            await self._remember_category(user_id, "income", fields["category"])
        return _income_response(await self.repo.apply_fields(txn, fields))

    async def delete_income(self, user_id: str, income_id: str) -> None:
        txn = get_or_404(await self.repo.get_transaction(user_id, income_id), "Income not found")
        await self.repo.delete_transaction(txn)

    # ==================================================================
    # Categories
    # ==================================================================

    async def category_options(self, user_id: str) -> CategoryOptions:
        stored = await self.repo.list_categories(user_id)
        expense = {name for name in DEFAULT_EXPENSE_CATEGORIES}
        income = {name for name in DEFAULT_INCOME_CATEGORIES}
        for category in stored:
            (income if category.txn_type == "income" else expense).add(category.name)
        return CategoryOptions(expense=sorted(expense), income=sorted(income))

    async def _remember_category(self, user_id: str, txn_type: str, name: str | None) -> None:
        """Persist a category the user typed, so type-select can offer it again."""
        clean = (name or "").strip()
        defaults = DEFAULT_EXPENSE_CATEGORIES if txn_type == "expense" else DEFAULT_INCOME_CATEGORIES
        if not clean or clean in defaults:
            return
        if await self.repo.get_category(user_id, txn_type, clean):
            return
        await self.repo.create_category(user_id, txn_type, clean[:32])

    async def create_category(self, user_id: str, txn_type: str, name: str) -> CategoryOptions:
        await self._remember_category(user_id, txn_type, name)
        return await self.category_options(user_id)

    # ==================================================================
    # Recurring definitions
    # ==================================================================

    async def list_recurring(self, user_id: str) -> list[RecurringResponse]:
        rows = await self.repo.list_recurring(user_id)
        return [RecurringResponse.model_validate(row) for row in rows]

    async def create_recurring(self, user_id: str, data: RecurringCreate) -> RecurringResponse:
        if data.end_date and data.end_date < data.start_date:
            raise BadRequestError("End date cannot be before start date")
        await self._remember_category(user_id, "expense", data.category)
        definition = await self.repo.add_recurring(
            FinanceRecurring(
                user_id=user_id,
                txn_type="expense",
                title=data.title,
                amount=data.amount,
                expense_kind=data.expense_kind,
                category=data.category,
                frequency="monthly",
                start_date=data.start_date,
                end_date=data.end_date,
                day_of_month=data.day_of_month,
                notes=data.notes,
            )
        )
        await self.run_generation(user_id)
        return RecurringResponse.model_validate(definition)

    async def update_recurring(
        self, user_id: str, recurring_id: str, data: RecurringUpdate
    ) -> RecurringResponse:
        definition = get_or_404(
            await self.repo.get_recurring(user_id, recurring_id), "Recurring expense not found"
        )
        fields = data.model_dump(exclude_unset=True)
        start = fields.get("start_date", definition.start_date)
        end = fields.get("end_date", definition.end_date)
        if end and end < start:
            raise BadRequestError("End date cannot be before start date")
        if "category" in fields:
            await self._remember_category(user_id, "expense", fields["category"])
        for key, value in fields.items():
            setattr(definition, key, value)
        await self.repo.flush()
        # Changing a definition never rewrites the expenses it already produced;
        # it only changes what gets generated from here on.
        await self.run_generation(user_id)
        return RecurringResponse.model_validate(definition)

    async def delete_recurring(self, user_id: str, recurring_id: str) -> None:
        """Remove the definition. Expenses it already generated are kept."""
        definition = get_or_404(
            await self.repo.get_recurring(user_id, recurring_id), "Recurring expense not found"
        )
        await self.repo.delete_recurring(definition)

    # ==================================================================
    # Loans
    # ==================================================================

    async def _loan_response(self, loan: Loan) -> LoanResponse:
        counts = await self.repo.emi_counts(loan.id)
        next_emi = await self.repo.next_pending_emi(loan.id)
        response = LoanResponse.model_validate(loan)
        response.emis_total = counts["total"]
        response.emis_paid = counts["paid"]
        response.emis_remaining = counts["pending"]
        response.next_due_date = next_emi.due_date if next_emi else None
        response.next_emi_amount = next_emi.amount if next_emi else None
        return response

    async def list_loans(self, user_id: str, status: str | None = None) -> list[LoanResponse]:
        await self.run_generation(user_id)
        return [await self._loan_response(loan) for loan in await self.repo.list_loans(user_id, status)]

    async def get_loan(self, user_id: str, loan_id: str) -> LoanResponse:
        loan = get_or_404(await self.repo.get_loan(user_id, loan_id), "Loan not found")
        return await self._loan_response(loan)

    async def loan_summary(self, user_id: str) -> LoanSummary:
        active, total = await self.repo.monthly_emi_obligation(user_id)
        return LoanSummary(active_loans=active, monthly_emi_total=total)

    async def create_loan(self, user_id: str, data: LoanCreate) -> LoanResponse:
        """Create the loan and its whole EMI schedule in one go.

        The user enters loan details once — never again month to month.
        """
        if data.emi_start_date < data.start_date:
            raise BadRequestError("EMI start date cannot be before the loan start date")
        loan = await self.repo.add_loan(
            Loan(
                user_id=user_id,
                name=data.name,
                lender=data.lender,
                principal_amount=data.principal_amount,
                emi_amount=data.emi_amount,
                interest_rate=data.interest_rate,
                start_date=data.start_date,
                emi_start_date=data.emi_start_date,
                tenure_months=data.tenure_months,
                emi_day=data.emi_day,
                notes=data.notes,
            )
        )
        await self._sync_schedule(loan)
        await self.run_generation(user_id)
        return await self._loan_response(loan)

    async def _sync_schedule(self, loan: Loan) -> None:
        """Create any EMI rows the schedule calls for that do not exist yet.

        Idempotent: existing emi_numbers are skipped, so re-running never
        duplicates a row (and the unique constraint backs that up).
        """
        existing = await self.repo.existing_emi_numbers(loan.id)
        schedule = emi_schedule(loan.emi_start_date, loan.emi_day, loan.tenure_months, loan.emi_amount)
        await self.repo.add_emis(
            [
                LoanEMI(loan_id=loan.id, emi_number=number, due_date=due, amount=amount)
                for number, due, amount in schedule
                if number not in existing
            ]
        )

    async def update_loan(self, user_id: str, loan_id: str, data: LoanUpdate) -> LoanResponse:
        loan = get_or_404(await self.repo.get_loan(user_id, loan_id), "Loan not found")
        fields = data.model_dump(exclude_unset=True)
        new_status = fields.pop("status", None)

        for key, value in fields.items():
            setattr(loan, key, value)

        # An EMI amount change applies to what has not been paid yet. Paid EMIs
        # and the expenses behind them are historical records — never rewritten.
        if "emi_amount" in fields:
            for emi in await self.repo.list_emis(loan.id):
                if emi.status == "PENDING":
                    emi.amount = loan.emi_amount

        if new_status and new_status != loan.status:
            await self._apply_status(loan, new_status)

        await self.repo.flush()
        return await self._loan_response(loan)

    async def _apply_status(self, loan: Loan, status: str) -> None:
        """Close or reopen a loan without destroying any history."""
        emis = await self.repo.list_emis(loan.id)
        if status == "CLOSED":
            loan.status = "CLOSED"
            loan.closed_at = self._today()
            # Pending instalments are cancelled, not deleted: paid history,
            # generated expenses and the schedule itself all survive.
            for emi in emis:
                if emi.status == "PENDING":
                    emi.status = "CANCELLED"
        else:
            loan.status = "ACTIVE"
            loan.closed_at = None
            for emi in emis:
                if emi.status == "CANCELLED":
                    emi.status = "PENDING"

    async def list_emis(self, user_id: str, loan_id: str) -> list[LoanEMIResponse]:
        get_or_404(await self.repo.get_loan(user_id, loan_id), "Loan not found")
        await self.run_generation(user_id)
        return [LoanEMIResponse.model_validate(emi) for emi in await self.repo.list_emis(loan_id)]

    async def mark_emi_paid(self, user_id: str, loan_id: str, emi_id: str, paid_date: date | None = None) -> LoanEMIResponse:
        loan = get_or_404(await self.repo.get_loan(user_id, loan_id), "Loan not found")
        emi = get_or_404(await self.repo.get_emi(loan_id, emi_id), "EMI not found")
        if emi.status == "CANCELLED":
            raise BadRequestError("Cancelled EMIs cannot be marked paid")

        emi.status = "PAID"
        emi.paid_date = paid_date or self._today()
        # Paying early still records the expense, so the money shows up the month
        # it actually left the account.
        await self._materialise_emi_expense(user_id, emi, loan)
        await self.repo.flush()
        return LoanEMIResponse.model_validate(emi)

    # ==================================================================
    # Legacy contracts — unchanged behaviour for existing consumers
    # ==================================================================

    async def list_transactions(
        self, user_id: str, txn_type: str | None = None, limit: int = 25, offset: int = 0
    ) -> tuple[list[TransactionResponse], int]:
        txns, total = await self.repo.list_transactions(user_id, txn_type, limit=limit, offset=offset)
        return [TransactionResponse.model_validate(t) for t in txns], total

    async def create_transaction(self, user_id: str, data: TransactionCreate) -> TransactionResponse:
        if data.txn_type not in ("income", "expense"):
            raise BadRequestError("txn_type must be income or expense")
        payload = data.model_copy()
        if payload.txn_type == "expense" and not payload.expense_kind:
            payload.expense_kind = "soft"
        txn = await self.repo.create_transaction(user_id, payload)
        return TransactionResponse.model_validate(txn)

    async def update_transaction(
        self, user_id: str, txn_id: str, data: TransactionUpdate
    ) -> TransactionResponse:
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
        return BudgetResponse.model_validate(await self.repo.upsert_budget(user_id, data))

    async def delete_budget(self, user_id: str, budget_id: str) -> None:
        get_or_404(await self.repo.delete_budget(user_id, budget_id), "Budget not found")

    async def summary(self, user_id: str) -> FinanceSummary:
        txns, _ = await self.repo.list_transactions(user_id, limit=None)
        budgets, _ = await self.list_budgets(user_id, limit=100)
        return FinanceSummary(
            total_income=sum(t.amount for t in txns if t.txn_type == "income"),
            total_expenses=sum(t.amount for t in txns if t.txn_type == "expense"),
            transaction_count=len(txns),
            budgets=budgets,
        )
