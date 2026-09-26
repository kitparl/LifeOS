import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { Loan, LoanPayload } from '../models/finance.models';
import { localIsoDate } from '../../../core/utils/date';

/**
 * Loan details are entered once. The EMI schedule is generated from them, so
 * there is nothing to re-enter month to month.
 */
@Component({
  selector: 'app-loan-form',
  standalone: true,
  imports: [ReactiveFormsModule, ModalComponent],
  template: `
    <app-modal
      [open]="open"
      [title]="loan ? 'Edit loan' : 'Add loan'"
      [maxWidth]="'560px'"
      (closed)="closed.emit()"
    >
      <form body class="grid gap-3 text-sm" [formGroup]="form" (ngSubmit)="submit()">
        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block">Loan name</label>
            <input class="input-field" formControlName="name" placeholder="Personal Loan" />
          </div>
          <div>
            <label class="mb-1 block">Lender</label>
            <input class="input-field" formControlName="lender" placeholder="HDFC Bank" />
          </div>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block">Loan amount</label>
            <input class="input-field" type="number" step="0.01" min="0" formControlName="principal_amount" />
          </div>
          <div>
            <label class="mb-1 block">EMI amount</label>
            <input class="input-field" type="number" step="0.01" min="0" formControlName="emi_amount" />
          </div>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block">Interest rate (%)</label>
            <input class="input-field" type="number" step="0.01" min="0" formControlName="interest_rate" />
          </div>
          <div>
            <label class="mb-1 block">EMI day</label>
            <input class="input-field" type="number" min="1" max="31" formControlName="emi_day" />
          </div>
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block">Start date</label>
            <input class="input-field" type="date" formControlName="start_date" [attr.disabled]="loan ? true : null" />
          </div>
          <div>
            <label class="mb-1 block">
              First EMI date
              @if (loan && loan.emis_paid > 0) {
                <span class="text-xs" style="color: var(--text-muted)"> (locked — an EMI is already paid)</span>
              }
            </label>
            <input
              class="input-field"
              type="date"
              formControlName="emi_start_date"
              [attr.disabled]="loan && loan.emis_paid > 0 ? true : null"
            />
          </div>
        </div>

        <div>
          <label class="mb-1 block">Schedule length</label>
          <div class="mb-2 flex flex-wrap gap-4 text-xs">
            <label class="flex items-center gap-2">
              <input type="radio" formControlName="scheduleMode" value="tenure" />
              Tenure (months)
            </label>
            <label class="flex items-center gap-2">
              <input type="radio" formControlName="scheduleMode" value="last_emi_date" />
              Last EMI date
            </label>
          </div>
          @if (form.value.scheduleMode === 'tenure') {
            <input class="input-field" type="number" min="1" formControlName="tenure_months" />
          } @else {
            <input class="input-field" type="date" formControlName="last_emi_date" />
          }
        </div>

        <div>
          <label class="mb-1 block">Notes</label>
          <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
        </div>

        @if (loan) {
          <p class="text-xs" style="color: var(--text-muted)">
            Changing the EMI amount updates upcoming instalments only. Changing the
            tenure/last EMI date or EMI day keeps paid EMIs exactly as recorded and
            only regenerates what's still upcoming.
          </p>
        } @else {
          <p class="text-xs" style="color: var(--text-muted)">
            The full EMI schedule is created automatically from the first EMI date,
            EMI day and tenure (or last EMI date).
          </p>
        }
      </form>

      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" (click)="closed.emit()">Cancel</button>
        <button type="button" class="btn-primary text-xs" [disabled]="form.invalid" (click)="submit()">
          {{ loan ? 'Save loan' : 'Create loan' }}
        </button>
      </div>
    </app-modal>
  `,
})
export class LoanFormComponent implements OnChanges {
  private readonly fb = inject(FormBuilder);

  @Input() open = false;
  @Input() loan: Loan | null = null;

  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly saved = new EventEmitter<LoanPayload>();

  readonly form = this.fb.nonNullable.group({
    name: ['', Validators.required],
    lender: [''],
    principal_amount: [0, [Validators.required, Validators.min(0.01)]],
    emi_amount: [0, [Validators.required, Validators.min(0.01)]],
    interest_rate: [0],
    start_date: [localIsoDate(), Validators.required],
    emi_start_date: [localIsoDate(), Validators.required],
    scheduleMode: ['tenure' as 'tenure' | 'last_emi_date', Validators.required],
    tenure_months: [12, [Validators.min(1)]],
    last_emi_date: [localIsoDate()],
    emi_day: [1, [Validators.required, Validators.min(1), Validators.max(31)]],
    notes: [''],
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['open'] && !changes['loan']) return;
    if (!this.open) return;

    if (this.loan) {
      this.form.setValue({
        name: this.loan.name,
        lender: this.loan.lender ?? '',
        principal_amount: this.loan.principal_amount,
        emi_amount: this.loan.emi_amount,
        interest_rate: this.loan.interest_rate ?? 0,
        start_date: this.loan.start_date,
        emi_start_date: this.loan.emi_start_date,
        scheduleMode: 'tenure',
        tenure_months: this.loan.tenure_months,
        last_emi_date: this.loan.next_due_date ?? localIsoDate(),
        emi_day: this.loan.emi_day,
        notes: this.loan.notes ?? '',
      });
    } else {
      const today = localIsoDate();
      this.form.reset({
        name: '',
        lender: '',
        principal_amount: 0,
        emi_amount: 0,
        interest_rate: 0,
        start_date: today,
        emi_start_date: today,
        scheduleMode: 'tenure',
        tenure_months: 12,
        last_emi_date: today,
        emi_day: Number(today.slice(8, 10)),
        notes: '',
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    const raw = this.form.getRawValue();
    const payload: LoanPayload = {
      name: raw.name.trim(),
      lender: raw.lender.trim() || null,
      principal_amount: Number(raw.principal_amount),
      emi_amount: Number(raw.emi_amount),
      interest_rate: Number(raw.interest_rate) || null,
      start_date: raw.start_date,
      emi_start_date: raw.emi_start_date,
      emi_day: Number(raw.emi_day),
      notes: raw.notes.trim() || null,
    };
    if (raw.scheduleMode === 'tenure') {
      payload.tenure_months = Number(raw.tenure_months);
    } else {
      payload.last_emi_date = raw.last_emi_date;
    }
    this.saved.emit(payload);
  }
}
