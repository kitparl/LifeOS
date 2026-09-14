import { Component, OnInit, inject, signal } from '@angular/core';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { PaginatedListState } from '../../shared/pagination/paginated-list.state';
import { TabHubComponent, TabHubItem } from '../../shared/tab-hub/tab-hub.component';
import { ExpenseFormComponent } from './components/expense-form.component';
import { ExpensesTabComponent } from './components/expenses-tab.component';
import { IncomeFormComponent } from './components/income-form.component';
import { IncomeTabComponent } from './components/income-tab.component';
import { LoanFormComponent } from './components/loan-form.component';
import { LoansTabComponent } from './components/loans-tab.component';
import { OverviewTabComponent } from './components/overview-tab.component';
import { PeriodFilterComponent } from './components/period-filter.component';
import { RecurringFormComponent } from './components/recurring-form.component';
import { RecurringTabComponent } from './components/recurring-tab.component';
import {
  Expense,
  ExpenseBreakdown,
  ExpenseKind,
  ExpensePayload,
  FinanceOverview,
  Income,
  IncomePayload,
  Loan,
  LoanEMI,
  LoanPayload,
  LoanSummary,
  PeriodSelection,
  RecurringExpense,
  RecurringPayload,
  UpcomingItem,
} from './models/finance.models';
import { FinanceService } from './services/finance.service';
import { defaultPeriod } from './utils/period';

type FinanceTab = 'overview' | 'income' | 'expenses' | 'recurring' | 'loans';

/**
 * Finance shell. Opens on the current calendar month and stays there — it never
 * jumps to another month just because this one is empty.
 */
@Component({
  selector: 'app-finance-page',
  standalone: true,
  imports: [
    TabHubComponent,
    PeriodFilterComponent,
    OverviewTabComponent,
    ExpensesTabComponent,
    IncomeTabComponent,
    RecurringTabComponent,
    LoansTabComponent,
    ExpenseFormComponent,
    IncomeFormComponent,
    RecurringFormComponent,
    LoanFormComponent,
  ],
  template: `
    <div class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 class="text-lg font-semibold">Finance</h1>
          @if (overview()) {
            <p class="text-sm" style="color: var(--text-muted)">{{ overview()!.label }}</p>
          }
        </div>
      </div>

      <app-finance-period-filter [period]="period()" (periodChange)="setPeriod($event)" />

      <app-tab-hub [tabs]="tabs" [activeId]="activeTab()" [wrap]="true" (tabChange)="setTab($event)" />

      @if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
      }

      @switch (activeTab()) {
        @case ('overview') {
          <app-finance-overview-tab
            [overview]="overview()"
            [breakdown]="breakdown()"
            [recentExpenses]="recentExpenses()"
            [upcoming]="upcoming()"
            [activeLoans]="activeLoans()"
            [loanSummary]="loanSummary()"
            (openLoans)="setTab('loans')"
          />
        }
        @case ('expenses') {
          <app-finance-expenses-tab
            [expenses]="expenses()"
            [categories]="expenseCategories()"
            [kind]="kindFilter()"
            [category]="categoryFilter()"
            [paging]="expensePaging"
            (add)="openExpenseForm(null)"
            (edit)="openExpenseForm($event)"
            (remove)="confirmDeleteExpense($event)"
            (kindChange)="setKindFilter($event)"
            (categoryChange)="setCategoryFilter($event)"
            (pageChange)="setExpensePage($event)"
          />
        }
        @case ('income') {
          <app-finance-income-tab
            [income]="income()"
            [paging]="incomePaging"
            (add)="openIncomeForm(null)"
            (edit)="openIncomeForm($event)"
            (remove)="confirmDeleteIncome($event)"
            (pageChange)="setIncomePage($event)"
          />
        }
        @case ('recurring') {
          <app-finance-recurring-tab
            [recurring]="recurring()"
            (add)="openRecurringForm(null)"
            (edit)="openRecurringForm($event)"
            (toggleActive)="toggleRecurring($event)"
            (remove)="confirmDeleteRecurring($event)"
          />
        }
        @case ('loans') {
          <app-finance-loans-tab
            [loans]="loans()"
            [summary]="loanSummary()"
            [expandedLoanId]="expandedLoanId()"
            [emis]="emis()"
            (add)="openLoanForm(null)"
            (edit)="openLoanForm($event)"
            (closeLoan)="confirmCloseLoan($event)"
            (reopen)="reopenLoan($event)"
            (toggleSchedule)="toggleSchedule($event)"
            (pay)="payEmi($event)"
          />
        }
      }

      <app-expense-form
        [open]="expenseFormOpen()"
        [expense]="editingExpense()"
        [categories]="expenseCategories()"
        (closed)="expenseFormOpen.set(false)"
        (saved)="saveExpense($event)"
        (categoryCreated)="rememberCategory($event, 'expense')"
      />

      <app-income-form
        [open]="incomeFormOpen()"
        [income]="editingIncome()"
        [categories]="incomeCategories()"
        (closed)="incomeFormOpen.set(false)"
        (saved)="saveIncome($event)"
        (categoryCreated)="rememberCategory($event, 'income')"
      />

      <app-recurring-form
        [open]="recurringFormOpen()"
        [recurring]="editingRecurring()"
        [categories]="expenseCategories()"
        (closed)="recurringFormOpen.set(false)"
        (saved)="saveRecurring($event)"
        (categoryCreated)="rememberCategory($event, 'expense')"
      />

      <app-loan-form
        [open]="loanFormOpen()"
        [loan]="editingLoan()"
        (closed)="loanFormOpen.set(false)"
        (saved)="saveLoan($event)"
      />
    </div>
  `,
})
export class FinancePageComponent implements OnInit {
  private readonly finance = inject(FinanceService);
  private readonly confirm = inject(ConfirmService);

  readonly tabs: TabHubItem[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'income', label: 'Income' },
    { id: 'expenses', label: 'Expenses' },
    { id: 'recurring', label: 'Recurring' },
    { id: 'loans', label: 'Loans' },
  ];

  readonly activeTab = signal<FinanceTab>('overview');
  readonly period = signal<PeriodSelection>(defaultPeriod());
  readonly error = signal<string | null>(null);

  readonly overview = signal<FinanceOverview | null>(null);
  readonly breakdown = signal<ExpenseBreakdown | null>(null);
  readonly recentExpenses = signal<Expense[]>([]);
  readonly upcoming = signal<UpcomingItem[]>([]);
  readonly loanSummary = signal<LoanSummary | null>(null);

  readonly expenses = signal<Expense[]>([]);
  readonly income = signal<Income[]>([]);
  readonly recurring = signal<RecurringExpense[]>([]);
  readonly loans = signal<Loan[]>([]);
  readonly emis = signal<LoanEMI[]>([]);
  readonly expandedLoanId = signal<string | null>(null);

  readonly expenseCategories = signal<string[]>([]);
  readonly incomeCategories = signal<string[]>([]);
  readonly kindFilter = signal<ExpenseKind | null>(null);
  readonly categoryFilter = signal<string | null>(null);

  readonly expenseFormOpen = signal(false);
  readonly incomeFormOpen = signal(false);
  readonly recurringFormOpen = signal(false);
  readonly loanFormOpen = signal(false);
  readonly editingExpense = signal<Expense | null>(null);
  readonly editingIncome = signal<Income | null>(null);
  readonly editingRecurring = signal<RecurringExpense | null>(null);
  readonly editingLoan = signal<Loan | null>(null);

  readonly expensePaging = new PaginatedListState();
  readonly incomePaging = new PaginatedListState();

  readonly activeLoans = signal<Loan[]>([]);

  ngOnInit(): void {
    this.loadCategories();
    this.loadAll();
  }

  // ---- Navigation / filters -------------------------------------------

  setTab(tab: string): void {
    this.activeTab.set(tab as FinanceTab);
    this.loadActiveTab();
  }

  setPeriod(period: PeriodSelection): void {
    this.period.set(period);
    this.expensePaging.setPage(1);
    this.incomePaging.setPage(1);
    this.loadAll();
  }

  setKindFilter(kind: ExpenseKind | null): void {
    this.kindFilter.set(kind);
    this.expensePaging.setPage(1);
    this.loadExpenses();
  }

  setCategoryFilter(category: string | null): void {
    this.categoryFilter.set(category);
    this.expensePaging.setPage(1);
    this.loadExpenses();
  }

  setExpensePage(page: number): void {
    this.expensePaging.setPage(page);
    this.loadExpenses();
  }

  setIncomePage(page: number): void {
    this.incomePaging.setPage(page);
    this.loadIncome();
  }

  // ---- Loading ---------------------------------------------------------

  private loadAll(): void {
    this.loadOverview();
    this.loadActiveTab();
  }

  private loadActiveTab(): void {
    switch (this.activeTab()) {
      case 'expenses':
        this.loadExpenses();
        break;
      case 'income':
        this.loadIncome();
        break;
      case 'recurring':
        this.loadRecurring();
        break;
      case 'loans':
        this.loadLoans();
        break;
      default:
        this.loadOverview();
    }
  }

  private loadOverview(): void {
    const period = this.period();
    this.finance.overview(period).subscribe({
      next: (data) => this.overview.set(data),
      error: () => this.error.set('Could not load the finance overview.'),
    });
    this.finance.breakdown(period).subscribe({ next: (data) => this.breakdown.set(data) });
    this.finance
      .listExpenses(period, { limit: 5, offset: 0 })
      .subscribe({ next: (result) => this.recentExpenses.set(result.items) });
    this.finance.upcoming(30).subscribe({ next: (items) => this.upcoming.set(items) });
    this.finance.loanSummary().subscribe({ next: (summary) => this.loanSummary.set(summary) });
    this.finance.listLoans('ACTIVE').subscribe({ next: (loans) => this.activeLoans.set(loans) });
  }

  private loadExpenses(): void {
    this.finance
      .listExpenses(this.period(), {
        kind: this.kindFilter(),
        category: this.categoryFilter(),
        limit: this.expensePaging.pageSize,
        offset: this.expensePaging.offset,
      })
      .subscribe({
        next: (result) => {
          this.expenses.set(result.items);
          this.expensePaging.total = result.total;
        },
        error: () => this.error.set('Could not load expenses.'),
      });
  }

  private loadIncome(): void {
    this.finance
      .listIncome(this.period(), {
        limit: this.incomePaging.pageSize,
        offset: this.incomePaging.offset,
      })
      .subscribe({
        next: (result) => {
          this.income.set(result.items);
          this.incomePaging.total = result.total;
        },
        error: () => this.error.set('Could not load income.'),
      });
  }

  private loadRecurring(): void {
    this.finance.listRecurring().subscribe({ next: (items) => this.recurring.set(items) });
  }

  private loadLoans(): void {
    this.finance.listLoans().subscribe({ next: (items) => this.loans.set(items) });
    this.finance.loanSummary().subscribe({ next: (summary) => this.loanSummary.set(summary) });
  }

  private loadCategories(): void {
    this.finance.categories().subscribe({
      next: (options) => {
        this.expenseCategories.set(options.expense);
        this.incomeCategories.set(options.income);
      },
    });
  }

  rememberCategory(name: string, type: 'expense' | 'income'): void {
    this.finance.createCategory(name, type).subscribe({
      next: (options) => {
        this.expenseCategories.set(options.expense);
        this.incomeCategories.set(options.income);
      },
    });
  }

  // ---- Expenses --------------------------------------------------------

  openExpenseForm(expense: Expense | null): void {
    this.editingExpense.set(expense);
    this.expenseFormOpen.set(true);
  }

  saveExpense(payload: ExpensePayload): void {
    const editing = this.editingExpense();
    const request = editing
      ? this.finance.updateExpense(editing.id, payload)
      : this.finance.createExpense(payload);
    request.subscribe({
      next: () => {
        this.expenseFormOpen.set(false);
        this.loadCategories();
        this.loadOverview();
        this.loadExpenses();
      },
      error: () => this.error.set('Could not save the expense.'),
    });
  }

  confirmDeleteExpense(expense: Expense): void {
    this.confirm
      .confirm(`Delete "${expense.title || expense.category}"?`, 'Delete expense')
      .then((confirmed) => {
        if (!confirmed) return;
        this.finance.deleteExpense(expense.id).subscribe({
          next: () => {
            this.loadOverview();
            this.loadExpenses();
          },
        });
      });
  }

  // ---- Income ----------------------------------------------------------

  openIncomeForm(income: Income | null): void {
    this.editingIncome.set(income);
    this.incomeFormOpen.set(true);
  }

  saveIncome(payload: IncomePayload): void {
    const editing = this.editingIncome();
    const request = editing
      ? this.finance.updateIncome(editing.id, payload)
      : this.finance.createIncome(payload);
    request.subscribe({
      next: () => {
        this.incomeFormOpen.set(false);
        this.loadCategories();
        this.loadOverview();
        this.loadIncome();
      },
      error: () => this.error.set('Could not save the income record.'),
    });
  }

  confirmDeleteIncome(income: Income): void {
    this.confirm
      .confirm(`Delete "${income.title || income.category}"?`, 'Delete income')
      .then((confirmed) => {
        if (!confirmed) return;
        this.finance.deleteIncome(income.id).subscribe({
          next: () => {
            this.loadOverview();
            this.loadIncome();
          },
        });
      });
  }

  // ---- Recurring -------------------------------------------------------

  openRecurringForm(recurring: RecurringExpense | null): void {
    this.editingRecurring.set(recurring);
    this.recurringFormOpen.set(true);
  }

  saveRecurring(payload: RecurringPayload): void {
    const editing = this.editingRecurring();
    const request = editing
      ? this.finance.updateRecurring(editing.id, payload)
      : this.finance.createRecurring(payload);
    request.subscribe({
      next: () => {
        this.recurringFormOpen.set(false);
        this.loadCategories();
        this.loadRecurring();
        this.loadOverview();
      },
      error: () => this.error.set('Could not save the recurring expense.'),
    });
  }

  toggleRecurring(item: RecurringExpense): void {
    this.finance.updateRecurring(item.id, { is_active: !item.is_active }).subscribe({
      next: () => {
        this.loadRecurring();
        this.loadOverview();
      },
    });
  }

  confirmDeleteRecurring(item: RecurringExpense): void {
    this.confirm
      .confirm(
        `Delete "${item.title}"? Expenses it already created are kept.`,
        'Delete recurring expense',
      )
      .then((confirmed) => {
        if (!confirmed) return;
        this.finance.deleteRecurring(item.id).subscribe({ next: () => this.loadRecurring() });
      });
  }

  // ---- Loans -----------------------------------------------------------

  openLoanForm(loan: Loan | null): void {
    this.editingLoan.set(loan);
    this.loanFormOpen.set(true);
  }

  saveLoan(payload: LoanPayload): void {
    const editing = this.editingLoan();
    const request = editing
      ? this.finance.updateLoan(editing.id, {
          name: payload.name,
          lender: payload.lender,
          principal_amount: payload.principal_amount,
          emi_amount: payload.emi_amount,
          interest_rate: payload.interest_rate,
          notes: payload.notes,
        })
      : this.finance.createLoan(payload);
    request.subscribe({
      next: () => {
        this.loanFormOpen.set(false);
        this.loadLoans();
        this.loadOverview();
      },
      error: () => this.error.set('Could not save the loan.'),
    });
  }

  confirmCloseLoan(loan: Loan): void {
    this.confirm
      .confirm(
        `Close "${loan.name}"? Pending EMIs are cancelled. Paid EMIs and their expenses are kept.`,
        'Close loan',
      )
      .then((confirmed) => {
        if (!confirmed) return;
        this.finance.updateLoan(loan.id, { status: 'CLOSED' }).subscribe({
          next: () => {
            this.loadLoans();
            this.refreshScheduleIfOpen(loan.id);
          },
        });
      });
  }

  reopenLoan(loan: Loan): void {
    this.finance.updateLoan(loan.id, { status: 'ACTIVE' }).subscribe({
      next: () => {
        this.loadLoans();
        this.refreshScheduleIfOpen(loan.id);
      },
    });
  }

  toggleSchedule(loan: Loan): void {
    if (this.expandedLoanId() === loan.id) {
      this.expandedLoanId.set(null);
      this.emis.set([]);
      return;
    }
    this.expandedLoanId.set(loan.id);
    this.finance.listEmis(loan.id).subscribe({ next: (items) => this.emis.set(items) });
  }

  payEmi(emi: LoanEMI): void {
    this.finance.payEmi(emi.loan_id, emi.id).subscribe({
      next: () => {
        this.loadLoans();
        this.loadOverview();
        this.refreshScheduleIfOpen(emi.loan_id);
      },
      error: () => this.error.set('Could not mark the EMI as paid.'),
    });
  }

  private refreshScheduleIfOpen(loanId: string): void {
    if (this.expandedLoanId() !== loanId) return;
    this.finance.listEmis(loanId).subscribe({ next: (items) => this.emis.set(items) });
  }
}
