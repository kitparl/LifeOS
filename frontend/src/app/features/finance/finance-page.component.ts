import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { PaginatedListState } from '../../shared/pagination/paginated-list.state';
import { FinanceSummary, FinanceTransaction } from './models/finance.models';
import { FinanceService } from './services/finance.service';

@Component({
  selector: 'app-finance-page',
  standalone: true,
  imports: [ReactiveFormsModule, DatePipe, ListPaginatorComponent],
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">Finance</h1>

      @if (summary) {
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="panel text-sm"><p class="text-gray-600">Income</p><p class="text-lg font-semibold text-green-700">{{ summary.total_income }}</p></div>
          <div class="panel text-sm"><p class="text-gray-600">Expenses</p><p class="text-lg font-semibold text-red-700">{{ summary.total_expenses }}</p></div>
          <div class="panel text-sm"><p class="text-gray-600">Net</p><p class="text-lg font-semibold">{{ summary.net }}</p></div>
        </div>
      }

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Add transaction</div>
        <form class="grid gap-2 p-3 text-sm sm:grid-cols-2" [formGroup]="txnForm" (ngSubmit)="addTxn()">
          <select class="input-field" formControlName="txn_type">
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
          <input class="input-field" type="number" step="0.01" formControlName="amount" placeholder="Amount" />
          <input class="input-field" formControlName="category" placeholder="Category" />
          <input class="input-field" type="date" formControlName="txn_date" />
          <input class="input-field sm:col-span-2" formControlName="description" placeholder="Description" />
          <button type="submit" class="btn-primary text-xs sm:col-span-2 !w-fit">Add</button>
        </form>
      </div>

      <div class="panel !p-0 overflow-hidden">
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (t of transactions; track t.id) {
            <li class="flex items-center justify-between gap-2 px-3 py-2">
              <div>
                <p>{{ t.description || t.category }} <span class="text-gray-500">({{ t.txn_type }})</span></p>
                <p class="text-xs text-gray-500">{{ t.txn_date | date }}</p>
              </div>
              <div class="flex items-center gap-2">
                <span [class.text-green-700]="t.txn_type === 'income'" [class.text-red-700]="t.txn_type === 'expense'">{{ t.amount }}</span>
                <button type="button" class="text-xs" style="color: var(--danger)" (click)="removeTxn(t.id)">Delete</button>
              </div>
            </li>
          }
        </ul>
        <app-list-paginator
          [total]="paging.total"
          [pageSize]="paging.pageSize"
          [currentPage]="paging.currentPage"
          (pageChange)="setPage($event)"
        />
      </div>
    </div>
  `,
})
export class FinancePageComponent implements OnInit {
  private readonly finance = inject(FinanceService);
  private readonly fb = inject(FormBuilder);

  summary: FinanceSummary | null = null;
  transactions: FinanceTransaction[] = [];
  readonly paging = new PaginatedListState();

  txnForm = this.fb.nonNullable.group({
    txn_type: ['expense'],
    amount: [0],
    category: ['other'],
    txn_date: [new Date().toISOString().slice(0, 10)],
    description: [''],
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.finance.summary().subscribe({ next: (s) => (this.summary = s) });
    this.finance.listTransactions({ limit: this.paging.pageSize, offset: this.paging.offset }).subscribe({
      next: (result) => {
        this.transactions = result.items;
        this.paging.total = result.total;
        this.clampPage();
      },
    });
  }

  setPage(page: number): void {
    this.paging.setPage(page);
    this.load();
  }

  private clampPage(): void {
    const totalPages = Math.max(1, Math.ceil(this.paging.total / this.paging.pageSize));
    if (this.paging.currentPage > totalPages) {
      this.paging.setPage(totalPages);
      this.load();
    }
  }

  addTxn(): void {
    const raw = this.txnForm.getRawValue();
    if (!raw.amount) return;
    this.finance.createTransaction({ ...raw, description: raw.description || null }).subscribe({
      next: () => {
        this.paging.setPage(1);
        this.load();
      },
    });
  }

  removeTxn(id: string): void {
    this.finance.deleteTransaction(id).subscribe({ next: () => this.load() });
  }
}
