import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CurrencyPreferencesService } from '../../../core/services/currency-preferences.service';
import { ListPaginatorComponent } from '../../../shared/pagination/list-paginator.component';
import { PaginatedListState } from '../../../shared/pagination/paginated-list.state';
import { Expense, ExpenseKind } from '../models/finance.models';

/** Expense list for the selected period, newest first, with All/Soft/Hard/Category filters. */
@Component({
  selector: 'app-finance-expenses-tab',
  standalone: true,
  imports: [DatePipe, ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center gap-2">
        <button
          type="button"
          class="text-xs"
          [class.btn-primary]="!kind"
          [class.btn-secondary]="kind"
          (click)="kindChange.emit(null)"
        >All</button>
        <button
          type="button"
          class="text-xs"
          [class.btn-primary]="kind === 'soft'"
          [class.btn-secondary]="kind !== 'soft'"
          (click)="kindChange.emit('soft')"
        >Soft</button>
        <button
          type="button"
          class="text-xs"
          [class.btn-primary]="kind === 'hard'"
          [class.btn-secondary]="kind !== 'hard'"
          (click)="kindChange.emit('hard')"
        >Hard</button>

        <select
          class="input-field !w-auto text-xs"
          [value]="category ?? ''"
          (change)="onCategory($event)"
        >
          <option value="">All categories</option>
          @for (option of categories; track option) {
            <option [value]="option">{{ option }}</option>
          }
        </select>

        <button type="button" class="btn-primary text-xs sm:ml-auto" (click)="add.emit()">
          + Add Expense
        </button>
      </div>

      <div class="panel !p-0 overflow-hidden">
        @if (expenses.length) {
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (expense of expenses; track expense.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2">
                <div class="min-w-0">
                  <p class="truncate">
                    {{ expense.title || expense.category }}
                    @if (expense.loan_emi_id) {
                      <span class="text-xs" style="color: var(--text-muted)">· from loan</span>
                    } @else if (expense.recurring_id) {
                      <span class="text-xs" style="color: var(--text-muted)">· recurring</span>
                    }
                  </p>
                  <p class="text-xs" style="color: var(--text-muted)">
                    {{ expense.txn_date | date: 'dd MMM' }} · {{ expense.category }}
                  </p>
                </div>
                <div class="flex shrink-0 items-center gap-2">
                  <span class="chip text-xs">{{ expense.expense_kind === 'hard' ? 'Hard' : 'Soft' }}</span>
                  <span class="font-medium">{{ money(expense.amount) }}</span>
                  <button type="button" class="text-xs" (click)="edit.emit(expense)">Edit</button>
                  <button
                    type="button"
                    class="text-xs"
                    style="color: var(--danger)"
                    (click)="remove.emit(expense)"
                  >Delete</button>
                </div>
              </li>
            }
          </ul>
          <app-list-paginator
            [total]="paging.total"
            [pageSize]="paging.pageSize"
            [currentPage]="paging.currentPage"
            (pageChange)="pageChange.emit($event)"
          />
        } @else {
          <p class="p-3 text-sm" style="color: var(--text-muted)">
            No expenses match this period and filter.
          </p>
        }
      </div>
    </div>
  `,
})
export class ExpensesTabComponent {
  private readonly currency = inject(CurrencyPreferencesService);

  @Input() expenses: Expense[] = [];
  @Input() categories: string[] = [];
  @Input() kind: ExpenseKind | null = null;
  @Input() category: string | null = null;
  @Input({ required: true }) paging!: PaginatedListState;

  @Output() readonly add = new EventEmitter<void>();
  @Output() readonly edit = new EventEmitter<Expense>();
  @Output() readonly remove = new EventEmitter<Expense>();
  @Output() readonly kindChange = new EventEmitter<ExpenseKind | null>();
  @Output() readonly categoryChange = new EventEmitter<string | null>();
  @Output() readonly pageChange = new EventEmitter<number>();

  onCategory(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.categoryChange.emit(value || null);
  }

  money(amount: number | null | undefined): string {
    return this.currency.format(amount);
  }
}
