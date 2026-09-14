import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CurrencyPreferencesService } from '../../../core/services/currency-preferences.service';
import { BarChartComponent } from '../../../shared/charts/bar-chart.component';
import { ChartPoint } from '../../../shared/charts/chart-types';
import {
  Expense,
  ExpenseBreakdown,
  FinanceOverview,
  Loan,
  LoanSummary,
  UpcomingItem,
} from '../models/finance.models';

/**
 * The default Finance view, in the order the module is meant to be read:
 * totals, soft vs hard, obligations, category breakdown, recent activity,
 * what is coming, active loans.
 *
 * There is deliberately no "remaining" or "savings" figure anywhere here.
 */
@Component({
  selector: 'app-finance-overview-tab',
  standalone: true,
  imports: [DatePipe, BarChartComponent],
  template: `
    <div class="space-y-4">
      @if (overview) {
        <div class="grid gap-3 sm:grid-cols-2">
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Income</p>
            <p class="text-lg font-semibold">{{ money(overview.total_income) }}</p>
          </div>
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Total Expenses</p>
            <p class="text-lg font-semibold">{{ money(overview.total_expenses) }}</p>
          </div>
        </div>

        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Soft Expenses</p>
            <p class="font-semibold">{{ money(overview.soft_expenses) }}</p>
          </div>
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Hard Expenses</p>
            <p class="font-semibold">{{ money(overview.hard_expenses) }}</p>
          </div>
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Loan EMI</p>
            <p class="font-semibold">{{ money(overview.loan_emi_expenses) }}</p>
          </div>
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Recurring Expenses</p>
            <p class="font-semibold">{{ money(overview.recurring_expenses) }}</p>
          </div>
        </div>
      }

      @if (loanSummary && loanSummary.active_loans > 0) {
        <div class="panel text-sm">
          <p class="font-semibold">Monthly obligation</p>
          <p style="color: var(--text-muted)">
            {{ loanSummary.active_loans }} active
            {{ loanSummary.active_loans === 1 ? 'loan' : 'loans' }} ·
            {{ money(loanSummary.monthly_emi_total) }} per month
          </p>
        </div>
      }

      <!-- Category breakdown -->
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Expenses by category</div>
        @if (breakdown && breakdown.categories.length) {
          <div class="p-3">
            <app-bar-chart [points]="chartPoints" title="Expenses by category" />
          </div>
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (row of breakdown.categories; track row.category) {
              <li class="flex items-center justify-between px-3 py-2">
                <span>{{ row.category }}</span>
                <span class="font-medium">{{ money(row.amount) }}</span>
              </li>
            }
          </ul>
        } @else {
          <p class="p-3 text-sm" style="color: var(--text-muted)">No expenses in this period.</p>
        }
      </div>

      <!-- Recent expenses -->
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Recent expenses</div>
        @if (recentExpenses.length) {
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (expense of recentExpenses; track expense.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2">
                <div class="min-w-0">
                  <p class="truncate">{{ expense.title || expense.category }}</p>
                  <p class="text-xs" style="color: var(--text-muted)">
                    {{ expense.txn_date | date: 'dd MMM' }} · {{ expense.category }}
                  </p>
                </div>
                <div class="flex shrink-0 items-center gap-2">
                  <span class="chip text-xs">{{ expense.expense_kind === 'hard' ? 'Hard' : 'Soft' }}</span>
                  <span class="font-medium">{{ money(expense.amount) }}</span>
                </div>
              </li>
            }
          </ul>
        } @else {
          <p class="p-3 text-sm" style="color: var(--text-muted)">Nothing recorded in this period yet.</p>
        }
      </div>

      <!-- Upcoming payments -->
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Upcoming payments</div>
        @if (upcoming.length) {
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (item of upcoming; track item.due_date + item.title) {
              <li class="flex items-center justify-between gap-2 px-3 py-2">
                <div class="min-w-0">
                  <p class="truncate">{{ item.title }}</p>
                  <p class="text-xs" style="color: var(--text-muted)">
                    {{ item.due_date | date: 'dd MMM' }} ·
                    {{ item.source === 'loan_emi' ? 'Loan EMI' : 'Recurring' }}
                  </p>
                </div>
                <span class="shrink-0 font-medium">{{ money(item.amount) }}</span>
              </li>
            }
          </ul>
        } @else {
          <p class="p-3 text-sm" style="color: var(--text-muted)">Nothing due in the next 30 days.</p>
        }
      </div>

      <!-- Active loans -->
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Active loans</div>
        @if (activeLoans.length) {
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (loan of activeLoans; track loan.id) {
              <li class="px-3 py-2">
                <div class="flex items-center justify-between gap-2">
                  <p class="truncate font-medium">{{ loan.name }}</p>
                  <span class="shrink-0">{{ money(loan.emi_amount) }}</span>
                </div>
                <p class="text-xs" style="color: var(--text-muted)">
                  {{ loan.emis_paid }} paid · {{ loan.emis_remaining }} remaining
                  @if (loan.next_due_date) {
                    · next {{ loan.next_due_date | date: 'dd MMM yyyy' }}
                  }
                </p>
              </li>
            }
          </ul>
        } @else {
          <p class="p-3 text-sm" style="color: var(--text-muted)">No active loans.</p>
        }
        <div class="border-t border-[var(--xp-border)] px-3 py-2 text-right">
          <button type="button" class="btn-secondary text-xs" (click)="openLoans.emit()">
            Manage loans
          </button>
        </div>
      </div>
    </div>
  `,
})
export class OverviewTabComponent {
  private readonly currency = inject(CurrencyPreferencesService);

  @Input() overview: FinanceOverview | null = null;
  @Input() breakdown: ExpenseBreakdown | null = null;
  @Input() recentExpenses: Expense[] = [];
  @Input() upcoming: UpcomingItem[] = [];
  @Input() activeLoans: Loan[] = [];
  @Input() loanSummary: LoanSummary | null = null;

  @Output() readonly openLoans = new EventEmitter<void>();

  get chartPoints(): ChartPoint[] {
    return (this.breakdown?.categories ?? []).map((row) => ({
      label: row.category,
      value: row.amount,
    }));
  }

  money(amount: number | null | undefined): string {
    return this.currency.format(amount);
  }
}
