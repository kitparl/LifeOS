import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { LoanForeclosurePayload } from '../models/finance.models';
import { todayIso } from '../utils/period';

/**
 * Records an early loan settlement. The foreclosure amount is entered by the
 * user for tracking only — never calculated from interest or principal.
 */
@Component({
  selector: 'app-foreclose-form',
  standalone: true,
  imports: [ReactiveFormsModule, ModalComponent],
  template: `
    <app-modal [open]="open" title="Foreclose Loan" [maxWidth]="'480px'" (closed)="closed.emit()">
      <form body class="grid gap-3 text-sm" [formGroup]="form" (ngSubmit)="submit()">
        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block">Foreclosure date</label>
            <input class="input-field" type="date" formControlName="foreclosure_date" />
          </div>
          <div>
            <label class="mb-1 block">Foreclosure amount</label>
            <input class="input-field" type="number" step="0.01" min="0.01" formControlName="foreclosure_amount" />
          </div>
        </div>

        <div>
          <label class="mb-1 block">Notes</label>
          <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
        </div>

        <p class="text-xs" style="color: var(--text-muted)">
          All remaining upcoming EMIs will be cancelled. Paid EMIs and their expenses are kept.
        </p>
      </form>

      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" (click)="closed.emit()">Cancel</button>
        <button type="button" class="btn-primary text-xs" [disabled]="form.invalid" (click)="submit()">
          Foreclose loan
        </button>
      </div>
    </app-modal>
  `,
})
export class ForecloseFormComponent implements OnChanges {
  private readonly fb = inject(FormBuilder);

  @Input() open = false;

  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly saved = new EventEmitter<LoanForeclosurePayload>();

  readonly form = this.fb.nonNullable.group({
    foreclosure_date: [todayIso(), Validators.required],
    foreclosure_amount: [0, [Validators.required, Validators.min(0.01)]],
    notes: [''],
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['open'] || !this.open) return;
    this.form.reset({ foreclosure_date: todayIso(), foreclosure_amount: 0, notes: '' });
  }

  submit(): void {
    if (this.form.invalid) return;
    const raw = this.form.getRawValue();
    this.saved.emit({
      foreclosure_date: raw.foreclosure_date,
      foreclosure_amount: Number(raw.foreclosure_amount),
      notes: raw.notes.trim() || null,
    });
  }
}
