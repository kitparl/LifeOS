import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { TypeSelectComponent } from '../../../shared/type-select/type-select.component';
import { Expense, ExpensePayload, RecurringPayload } from '../models/finance.models';
import { localIsoDate } from '../../../core/utils/date';

/** Add/edit an expense. Date defaults to today so entry stays fast. */
@Component({
  selector: 'app-expense-form',
  standalone: true,
  imports: [ReactiveFormsModule, ModalComponent, TypeSelectComponent],
  template: `
    <app-modal
      [open]="open"
      [title]="expense ? 'Edit expense' : 'Add expense'"
      [maxWidth]="'520px'"
      (closed)="closed.emit()"
    >
      <form body class="grid gap-3 text-sm" [formGroup]="form" (ngSubmit)="submit()">
        <div>
          <label class="mb-1 block">Title</label>
          <input class="input-field" formControlName="title" placeholder="Zepto" />
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block">Amount</label>
            <input class="input-field" type="number" step="0.01" min="0" formControlName="amount" />
          </div>
          <div>
            <label class="mb-1 block">Date</label>
            <input class="input-field" type="date" formControlName="txn_date" />
          </div>
        </div>

        <div>
          <label class="mb-1 block">Type</label>
          <div class="flex gap-2">
            <button
              type="button"
              class="text-xs"
              [class.btn-primary]="form.controls.expense_kind.value === 'soft'"
              [class.btn-secondary]="form.controls.expense_kind.value !== 'soft'"
              [disabled]="isEmiExpense"
              (click)="form.controls.expense_kind.setValue('soft')"
            >Soft Expense</button>
            <button
              type="button"
              class="text-xs"
              [class.btn-primary]="form.controls.expense_kind.value === 'hard'"
              [class.btn-secondary]="form.controls.expense_kind.value !== 'hard'"
              (click)="form.controls.expense_kind.setValue('hard')"
            >Hard Expense</button>
          </div>
          @if (isEmiExpense) {
            <p class="mt-1 text-xs" style="color: var(--text-muted)">
              Loan EMI expenses are always Hard expenses.
            </p>
          }
        </div>

        <div>
          <label class="mb-1 block">Category</label>
          <app-type-select
            formControlName="category"
            placeholder="Select or create a category…"
            [options]="categories"
            (created)="categoryCreated.emit($event)"
          />
        </div>

        @if (!expense) {
          <div class="rounded-md border p-3" style="border-color: var(--xp-border)">
            <label class="flex items-center gap-2">
              <input type="checkbox" formControlName="recurring" />
              Repeat monthly
            </label>
            @if (form.controls.recurring.value) {
              <div class="mt-3 grid gap-3 sm:grid-cols-2">
                <div>
                  <label class="mb-1 block">End date (optional)</label>
                  <input class="input-field" type="date" formControlName="end_date" />
                </div>
              </div>
              <p class="mt-2 text-xs" style="color: var(--text-muted)">
                Repeats on the {{ dayOfMonthLabel }} of every month from this date onwards.
                Manage or cancel it later from the Recurring tab.
              </p>
            }
          </div>
        }

        <div>
          <label class="mb-1 block">Notes</label>
          <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
        </div>
      </form>

      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" (click)="closed.emit()">Cancel</button>
        <button type="button" class="btn-primary text-xs" [disabled]="form.invalid" (click)="submit()">
          {{ expense ? 'Save expense' : form.controls.recurring.value ? 'Add recurring expense' : 'Add expense' }}
        </button>
      </div>
    </app-modal>
  `,
})
export class ExpenseFormComponent implements OnChanges {
  private readonly fb = inject(FormBuilder);

  @Input() open = false;
  @Input() expense: Expense | null = null;
  @Input() categories: string[] = [];

  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly saved = new EventEmitter<ExpensePayload>();
  @Output() readonly savedRecurring = new EventEmitter<RecurringPayload>();
  @Output() readonly categoryCreated = new EventEmitter<string>();

  readonly form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    amount: [0, [Validators.required, Validators.min(0.01)]],
    txn_date: [localIsoDate(), Validators.required],
    expense_kind: ['soft' as 'soft' | 'hard', Validators.required],
    category: ['Other'],
    recurring: [false],
    end_date: [''],
    notes: [''],
  });

  get isEmiExpense(): boolean {
    return !!this.expense?.loan_emi_id;
  }

  /** Ordinal day-of-month the recurring definition would repeat on, from the chosen date. */
  get dayOfMonthLabel(): string {
    const day = this.dayOfMonth(this.form.controls.txn_date.value);
    if (day % 10 === 1 && day !== 11) return `${day}st`;
    if (day % 10 === 2 && day !== 12) return `${day}nd`;
    if (day % 10 === 3 && day !== 13) return `${day}rd`;
    return `${day}th`;
  }

  private dayOfMonth(isoDate: string): number {
    const day = Number(isoDate.split('-')[2]);
    return Number.isFinite(day) && day > 0 ? day : 1;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['open'] && !changes['expense']) return;
    if (!this.open) return;

    if (this.expense) {
      this.form.setValue({
        title: this.expense.title ?? '',
        amount: this.expense.amount,
        txn_date: this.expense.txn_date,
        expense_kind: this.expense.expense_kind ?? 'soft',
        category: this.expense.category,
        recurring: false,
        end_date: '',
        notes: this.expense.notes ?? '',
      });
    } else {
      this.form.reset({
        title: '',
        amount: 0,
        txn_date: localIsoDate(),
        expense_kind: 'soft',
        category: 'Other',
        recurring: false,
        end_date: '',
        notes: '',
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    const raw = this.form.getRawValue();

    if (!this.expense && raw.recurring) {
      this.savedRecurring.emit({
        title: raw.title.trim(),
        amount: Number(raw.amount),
        expense_kind: raw.expense_kind,
        category: raw.category || 'Other',
        start_date: raw.txn_date,
        end_date: raw.end_date || null,
        day_of_month: this.dayOfMonth(raw.txn_date),
        notes: raw.notes.trim() || null,
      });
      return;
    }

    this.saved.emit({
      title: raw.title.trim(),
      amount: Number(raw.amount),
      txn_date: raw.txn_date,
      expense_kind: raw.expense_kind,
      category: raw.category || 'Other',
      notes: raw.notes.trim() || null,
    });
  }
}
