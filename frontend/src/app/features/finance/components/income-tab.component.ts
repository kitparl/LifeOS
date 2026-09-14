import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CurrencyPreferencesService } from '../../../core/services/currency-preferences.service';
import { ListPaginatorComponent } from '../../../shared/pagination/list-paginator.component';
import { PaginatedListState } from '../../../shared/pagination/paginated-list.state';
import { Income } from '../models/finance.models';

/** Income records for the selected period. Context only — nothing is derived from these. */
@Component({
  selector: 'app-finance-income-tab',
  standalone: true,
  imports: [DatePipe, ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <div class="flex justify-end">
        <button type="button" class="btn-primary text-xs" (click)="add.emit()">+ Add Income</button>
      </div>

      <div class="panel !p-0 overflow-hidden">
        @if (income.length) {
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (record of income; track record.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2">
                <div class="min-w-0">
                  <p class="truncate">
                    {{ record.title || record.category }}
                    @if (record.is_recurring) {
                      <span class="text-xs" style="color: var(--text-muted)">· recurring</span>
                    }
                  </p>
                  <p class="text-xs" style="color: var(--text-muted)">
                    {{ record.txn_date | date: 'dd MMM' }} · {{ record.category }}
                  </p>
                </div>
                <div class="flex shrink-0 items-center gap-2">
                  <span class="font-medium">{{ money(record.amount) }}</span>
                  <button type="button" class="text-xs" (click)="edit.emit(record)">Edit</button>
                  <button
                    type="button"
                    class="text-xs"
                    style="color: var(--danger)"
                    (click)="remove.emit(record)"
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
          <p class="p-3 text-sm" style="color: var(--text-muted)">No income recorded in this period.</p>
        }
      </div>
    </div>
  `,
})
export class IncomeTabComponent {
  private readonly currency = inject(CurrencyPreferencesService);

  @Input() income: Income[] = [];
  @Input({ required: true }) paging!: PaginatedListState;

  @Output() readonly add = new EventEmitter<void>();
  @Output() readonly edit = new EventEmitter<Income>();
  @Output() readonly remove = new EventEmitter<Income>();
  @Output() readonly pageChange = new EventEmitter<number>();

  money(amount: number | null | undefined): string {
    return this.currency.format(amount);
  }
}
