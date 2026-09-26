import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { LoanPartPaymentPayload } from '../models/finance.models';
import { localIsoDate } from '../../../core/utils/date';

/**
 * Records a part-payment as a tracking event. The user picks whether it
 * reduces the future EMI or the remaining tenure, and enters the new value
 * directly — nothing here is calculated from interest or principal.
 */
@Component({
  selector: 'app-part-payment-form',
  standalone: true,
  imports: [ReactiveFormsModule, ModalComponent],
  template: `
    <app-modal [open]="open" title="Make Part Payment" [maxWidth]="'480px'" (closed)="closed.emit()">
      <form body class="grid gap-3 text-sm" [formGroup]="form" (ngSubmit)="submit()">
        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block">Payment date</label>
            <input class="input-field" type="date" formControlName="payment_date" />
          </div>
          <div>
            <label class="mb-1 block">Part payment amount</label>
            <input class="input-field" type="number" step="0.01" min="0.01" formControlName="amount" />
          </div>
        </div>

        <div>
          <label class="mb-1 block">Part payment impact</label>
          <div class="flex flex-wrap gap-4">
            <label class="flex items-center gap-2">
              <input type="radio" formControlName="impact" value="REDUCE_TENURE" />
              Reduce Tenure
            </label>
            <label class="flex items-center gap-2">
              <input type="radio" formControlName="impact" value="REDUCE_EMI" />
              Reduce EMI
            </label>
          </div>
        </div>

        @if (form.value.impact === 'REDUCE_TENURE') {
          <div>
            <label class="mb-1 block">New tenure (total EMIs)</label>
            <input class="input-field" type="number" min="1" formControlName="new_tenure_months" />
            <p class="mt-1 text-xs" style="color: var(--text-muted)">
              EMI amount stays the same; the remaining schedule is regenerated to finish in this many
              instalments total.
            </p>
          </div>
        } @else {
          <div>
            <label class="mb-1 block">New EMI amount</label>
            <input class="input-field" type="number" step="0.01" min="0.01" formControlName="new_emi_amount" />
            <p class="mt-1 text-xs" style="color: var(--text-muted)">
              Applies to upcoming instalments only — paid EMIs are never rewritten.
            </p>
          </div>
        }

        <div>
          <label class="mb-1 block">Notes</label>
          <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
        </div>
      </form>

      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" (click)="closed.emit()">Cancel</button>
        <button type="button" class="btn-primary text-xs" [disabled]="!canSubmit()" (click)="submit()">
          Save part payment
        </button>
      </div>
    </app-modal>
  `,
})
export class PartPaymentFormComponent implements OnChanges {
  private readonly fb = inject(FormBuilder);

  @Input() open = false;

  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly saved = new EventEmitter<LoanPartPaymentPayload>();

  // new_tenure_months / new_emi_amount are validated conditionally in canSubmit() —
  // only whichever one the chosen impact actually uses, not both unconditionally.
  readonly form = this.fb.nonNullable.group({
    payment_date: [localIsoDate(), Validators.required],
    amount: [0, [Validators.required, Validators.min(0.01)]],
    impact: ['REDUCE_TENURE' as 'REDUCE_TENURE' | 'REDUCE_EMI', Validators.required],
    new_tenure_months: [1],
    new_emi_amount: [0],
    notes: [''],
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['open'] || !this.open) return;
    this.form.reset({
      payment_date: localIsoDate(),
      amount: 0,
      impact: 'REDUCE_TENURE',
      new_tenure_months: 1,
      new_emi_amount: 0,
      notes: '',
    });
  }

  canSubmit(): boolean {
    if (this.form.invalid) return false;
    const raw = this.form.getRawValue();
    return raw.impact === 'REDUCE_TENURE'
      ? Number(raw.new_tenure_months) >= 1
      : Number(raw.new_emi_amount) > 0;
  }

  submit(): void {
    if (!this.canSubmit()) return;
    const raw = this.form.getRawValue();
    const payload: LoanPartPaymentPayload = {
      payment_date: raw.payment_date,
      amount: Number(raw.amount),
      impact: raw.impact,
      notes: raw.notes.trim() || null,
    };
    if (raw.impact === 'REDUCE_TENURE') {
      payload.new_tenure_months = Number(raw.new_tenure_months);
    } else {
      payload.new_emi_amount = Number(raw.new_emi_amount);
    }
    this.saved.emit(payload);
  }
}
