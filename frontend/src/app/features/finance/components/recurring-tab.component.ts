import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CurrencyPreferencesService } from '../../../core/services/currency-preferences.service';
import { RecurringExpense } from '../models/finance.models';

/**
 * Recurring definitions. Deactivating one stops future generation; the expenses
 * it already produced stay exactly where they are.
 */
@Component({
  selector: 'app-finance-recurring-tab',
  standalone: true,
  imports: [DatePipe],
  template: `
    <div class="space-y-3">
      <div class="flex justify-end">
        <button type="button" class="btn-primary text-xs" (click)="add.emit()">
          + Add Recurring Expense
        </button>
      </div>

      <div class="panel !p-0 overflow-hidden">
        @if (recurring.length) {
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (item of recurring; track item.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2">
                <div class="min-w-0">
                  <p class="truncate">
                    {{ item.title }}
                    @if (!item.is_active) {
                      <span class="text-xs" style="color: var(--text-muted)">· inactive</span>
                    }
                  </p>
                  <p class="text-xs" style="color: var(--text-muted)">
                    Day {{ item.day_of_month }} · {{ item.category }} ·
                    from {{ item.start_date | date: 'dd MMM yyyy' }}
                    @if (item.end_date) {
                      until {{ item.end_date | date: 'dd MMM yyyy' }}
                    }
                  </p>
                </div>
                <div class="flex shrink-0 items-center gap-2">
                  <span class="chip text-xs">{{ item.expense_kind === 'hard' ? 'Hard' : 'Soft' }}</span>
                  <span class="font-medium">{{ money(item.amount) }}</span>
                  <button type="button" class="text-xs" (click)="toggleActive.emit(item)">
                    {{ item.is_active ? 'Pause' : 'Resume' }}
                  </button>
                  <button type="button" class="text-xs" (click)="edit.emit(item)">Edit</button>
                  <button
                    type="button"
                    class="text-xs"
                    style="color: var(--danger)"
                    (click)="remove.emit(item)"
                  >Delete</button>
                </div>
              </li>
            }
          </ul>
        } @else {
          <p class="p-3 text-sm" style="color: var(--text-muted)">
            No recurring expenses yet.
          </p>
        }
      </div>

      <p class="text-xs" style="color: var(--text-muted)">
        Deleting a definition stops future generation. Expenses it already created are kept.
      </p>
    </div>
  `,
})
export class RecurringTabComponent {
  private readonly currency = inject(CurrencyPreferencesService);

  @Input() recurring: RecurringExpense[] = [];

  @Output() readonly add = new EventEmitter<void>();
  @Output() readonly edit = new EventEmitter<RecurringExpense>();
  @Output() readonly toggleActive = new EventEmitter<RecurringExpense>();
  @Output() readonly remove = new EventEmitter<RecurringExpense>();

  money(amount: number | null | undefined): string {
    return this.currency.format(amount);
  }
}
