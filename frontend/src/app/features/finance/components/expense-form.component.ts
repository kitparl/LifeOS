import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { TypeSelectComponent } from '../../../shared/type-select/type-select.component';
import { Expense, ExpensePayload } from '../models/finance.models';
import { todayIso } from '../utils/period';

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

        <div>
          <label class="mb-1 block">Notes</label>
          <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
        </div>
      </form>

      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" (click)="closed.emit()">Cancel</button>
        <button type="button" class="btn-primary text-xs" [disabled]="form.invalid" (click)="submit()">
          {{ expense ? 'Save expense' : 'Add expense' }}
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
  @Output() readonly categoryCreated = new EventEmitter<string>();

  readonly form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    amount: [0, [Validators.required, Validators.min(0.01)]],
    txn_date: [todayIso(), Validators.required],
    expense_kind: ['soft' as 'soft' | 'hard', Validators.required],
    category: ['Other'],
    notes: [''],
  });

  get isEmiExpense(): boolean {
    return !!this.expense?.loan_emi_id;
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
        notes: this.expense.notes ?? '',
      });
    } else {
      this.form.reset({
        title: '',
        amount: 0,
        txn_date: todayIso(),
        expense_kind: 'soft',
        category: 'Other',
        notes: '',
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    const raw = this.form.getRawValue();
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
