import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { TypeSelectComponent } from '../../../shared/type-select/type-select.component';
import { Income, IncomePayload } from '../models/finance.models';
import { localIsoDate } from '../../../core/utils/date';

/** Add/edit an income record. Income is context only — nothing is derived from it. */
@Component({
  selector: 'app-income-form',
  standalone: true,
  imports: [ReactiveFormsModule, ModalComponent, TypeSelectComponent],
  template: `
    <app-modal
      [open]="open"
      [title]="income ? 'Edit income' : 'Add income'"
      [maxWidth]="'520px'"
      (closed)="closed.emit()"
    >
      <form body class="grid gap-3 text-sm" [formGroup]="form" (ngSubmit)="submit()">
        <div>
          <label class="mb-1 block">Title</label>
          <input class="input-field" formControlName="title" placeholder="Salary" />
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
          <label class="mb-1 block">Source</label>
          <app-type-select
            formControlName="category"
            placeholder="Select or create a source…"
            [options]="categories"
            (created)="categoryCreated.emit($event)"
          />
        </div>

        <label class="flex items-center gap-2">
          <input type="checkbox" formControlName="is_recurring" />
          Recurring income
        </label>

        <div>
          <label class="mb-1 block">Notes</label>
          <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
        </div>
      </form>

      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" (click)="closed.emit()">Cancel</button>
        <button type="button" class="btn-primary text-xs" [disabled]="form.invalid" (click)="submit()">
          {{ income ? 'Save income' : 'Add income' }}
        </button>
      </div>
    </app-modal>
  `,
})
export class IncomeFormComponent implements OnChanges {
  private readonly fb = inject(FormBuilder);

  @Input() open = false;
  @Input() income: Income | null = null;
  @Input() categories: string[] = [];

  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly saved = new EventEmitter<IncomePayload>();
  @Output() readonly categoryCreated = new EventEmitter<string>();

  readonly form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    amount: [0, [Validators.required, Validators.min(0.01)]],
    txn_date: [localIsoDate(), Validators.required],
    category: ['Salary'],
    is_recurring: [false],
    notes: [''],
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['open'] && !changes['income']) return;
    if (!this.open) return;

    if (this.income) {
      this.form.setValue({
        title: this.income.title ?? '',
        amount: this.income.amount,
        txn_date: this.income.txn_date,
        category: this.income.category,
        is_recurring: this.income.is_recurring,
        notes: this.income.notes ?? '',
      });
    } else {
      this.form.reset({
        title: '',
        amount: 0,
        txn_date: localIsoDate(),
        category: 'Salary',
        is_recurring: false,
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
      category: raw.category || 'Other Income',
      is_recurring: raw.is_recurring,
      notes: raw.notes.trim() || null,
    });
  }
}
