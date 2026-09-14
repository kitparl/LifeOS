import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { TypeSelectComponent } from '../../../shared/type-select/type-select.component';
import { RecurringExpense, RecurringPayload } from '../models/finance.models';
import { startOfMonthIso } from '../utils/period';

/**
 * A recurring definition. It is not an expense — it generates one expense per
 * month, and those generated rows are what the totals count.
 */
@Component({
  selector: 'app-recurring-form',
  standalone: true,
  imports: [ReactiveFormsModule, ModalComponent, TypeSelectComponent],
  template: `
    <app-modal
      [open]="open"
      [title]="recurring ? 'Edit recurring expense' : 'Add recurring expense'"
      [maxWidth]="'520px'"
      (closed)="closed.emit()"
    >
      <form body class="grid gap-3 text-sm" [formGroup]="form" (ngSubmit)="submit()">
        <div>
          <label class="mb-1 block">Title</label>
          <input class="input-field" formControlName="title" placeholder="Rent" />
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block">Amount</label>
            <input class="input-field" type="number" step="0.01" min="0" formControlName="amount" />
          </div>
          <div>
            <label class="mb-1 block">Day of month</label>
            <input class="input-field" type="number" min="1" max="31" formControlName="day_of_month" />
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

        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block">Start date</label>
            <input class="input-field" type="date" formControlName="start_date" />
          </div>
          <div>
            <label class="mb-1 block">End date (optional)</label>
            <input class="input-field" type="date" formControlName="end_date" />
          </div>
        </div>

        <div>
          <label class="mb-1 block">Notes</label>
          <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
        </div>

        <p class="text-xs" style="color: var(--text-muted)">
          Monthly expenses are generated automatically from the start date onwards.
          A day past the end of a short month falls back to that month's last day.
        </p>
      </form>

      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" (click)="closed.emit()">Cancel</button>
        <button type="button" class="btn-primary text-xs" [disabled]="form.invalid" (click)="submit()">
          {{ recurring ? 'Save' : 'Add recurring expense' }}
        </button>
      </div>
    </app-modal>
  `,
})
export class RecurringFormComponent implements OnChanges {
  private readonly fb = inject(FormBuilder);

  @Input() open = false;
  @Input() recurring: RecurringExpense | null = null;
  @Input() categories: string[] = [];

  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly saved = new EventEmitter<RecurringPayload>();
  @Output() readonly categoryCreated = new EventEmitter<string>();

  readonly form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    amount: [0, [Validators.required, Validators.min(0.01)]],
    expense_kind: ['hard' as 'soft' | 'hard', Validators.required],
    category: ['Other'],
    start_date: [startOfMonthIso(), Validators.required],
    end_date: [''],
    day_of_month: [1, [Validators.required, Validators.min(1), Validators.max(31)]],
    notes: [''],
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['open'] && !changes['recurring']) return;
    if (!this.open) return;

    if (this.recurring) {
      this.form.setValue({
        title: this.recurring.title,
        amount: this.recurring.amount,
        expense_kind: this.recurring.expense_kind,
        category: this.recurring.category,
        start_date: this.recurring.start_date,
        end_date: this.recurring.end_date ?? '',
        day_of_month: this.recurring.day_of_month,
        notes: this.recurring.notes ?? '',
      });
    } else {
      this.form.reset({
        title: '',
        amount: 0,
        expense_kind: 'hard',
        category: 'Other',
        start_date: startOfMonthIso(),
        end_date: '',
        day_of_month: 1,
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
      expense_kind: raw.expense_kind,
      category: raw.category || 'Other',
      start_date: raw.start_date,
      end_date: raw.end_date || null,
      day_of_month: Number(raw.day_of_month),
      notes: raw.notes.trim() || null,
    });
  }
}
