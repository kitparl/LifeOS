import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CurrencyPreferencesService } from '../../../core/services/currency-preferences.service';
import { Loan, LoanEMI, LoanSummary } from '../models/finance.models';

/**
 * Loans and their EMI schedules. Paid/remaining counts and the next due date
 * come from the EMI records themselves, so they can never disagree with them.
 */
@Component({
  selector: 'app-finance-loans-tab',
  standalone: true,
  imports: [DatePipe],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center gap-2">
        @if (summary) {
          <p class="text-sm" style="color: var(--text-muted)">
            {{ summary.active_loans }} active
            {{ summary.active_loans === 1 ? 'loan' : 'loans' }} ·
            {{ money(summary.monthly_emi_total) }} monthly obligation
          </p>
        }
        <button type="button" class="btn-primary text-xs sm:ml-auto" (click)="add.emit()">
          + Add Loan
        </button>
      </div>

      @if (loans.length) {
        @for (loan of loans; track loan.id) {
          <div class="panel !p-0 overflow-hidden">
            <div class="title-bar rounded-none border-x-0 border-t-0 flex items-center justify-between gap-2">
              <span class="truncate">{{ loan.name }}</span>
              <span class="text-xs">{{ loan.status === 'ACTIVE' ? 'Active' : 'Closed' }}</span>
            </div>

            <div class="grid gap-2 p-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p class="text-xs" style="color: var(--text-muted)">EMI</p>
                <p class="font-medium">{{ money(loan.emi_amount) }}</p>
              </div>
              <div>
                <p class="text-xs" style="color: var(--text-muted)">EMIs Paid</p>
                <p class="font-medium">{{ loan.emis_paid }}</p>
              </div>
              <div>
                <p class="text-xs" style="color: var(--text-muted)">Remaining EMIs</p>
                <p class="font-medium">{{ loan.emis_remaining }}</p>
              </div>
              <div>
                <p class="text-xs" style="color: var(--text-muted)">Next EMI</p>
                <p class="font-medium">
                  {{ loan.next_due_date ? (loan.next_due_date | date: 'dd MMM yyyy') : '—' }}
                </p>
              </div>
            </div>

            <div class="flex flex-wrap gap-2 border-t border-[var(--xp-border)] px-3 py-2">
              <button type="button" class="btn-secondary text-xs" (click)="toggleSchedule.emit(loan)">
                {{ expandedLoanId === loan.id ? 'Hide schedule' : 'View schedule' }}
              </button>
              <button type="button" class="btn-secondary text-xs" (click)="edit.emit(loan)">Edit</button>
              @if (loan.status === 'ACTIVE') {
                <button type="button" class="btn-secondary text-xs" (click)="closeLoan.emit(loan)">
                  Close loan
                </button>
              } @else {
                <button type="button" class="btn-secondary text-xs" (click)="reopen.emit(loan)">
                  Reopen
                </button>
              }
            </div>

            @if (expandedLoanId === loan.id) {
              <ul class="divide-y divide-[var(--xp-border)] border-t border-[var(--xp-border)] text-sm">
                @for (emi of emis; track emi.id) {
                  <li class="flex items-center justify-between gap-2 px-3 py-2">
                    <div class="min-w-0">
                      <p>EMI {{ emi.emi_number }} · {{ emi.due_date | date: 'dd MMM yyyy' }}</p>
                      @if (emi.paid_date) {
                        <p class="text-xs" style="color: var(--text-muted)">
                          Paid {{ emi.paid_date | date: 'dd MMM yyyy' }}
                        </p>
                      }
                    </div>
                    <div class="flex shrink-0 items-center gap-2">
                      <span class="chip text-xs">{{ statusLabel(emi) }}</span>
                      <span class="font-medium">{{ money(emi.amount) }}</span>
                      @if (emi.status === 'PENDING') {
                        <button type="button" class="text-xs" (click)="pay.emit(emi)">Mark paid</button>
                      }
                    </div>
                  </li>
                }
              </ul>
            }
          </div>
        }
      } @else {
        <div class="panel text-sm" style="color: var(--text-muted)">
          No loans yet. Add one and its EMI schedule is created for you.
        </div>
      }
    </div>
  `,
})
export class LoansTabComponent {
  private readonly currency = inject(CurrencyPreferencesService);

  @Input() loans: Loan[] = [];
  @Input() summary: LoanSummary | null = null;
  @Input() expandedLoanId: string | null = null;
  @Input() emis: LoanEMI[] = [];

  @Output() readonly add = new EventEmitter<void>();
  @Output() readonly edit = new EventEmitter<Loan>();
  @Output() readonly closeLoan = new EventEmitter<Loan>();
  @Output() readonly reopen = new EventEmitter<Loan>();
  @Output() readonly toggleSchedule = new EventEmitter<Loan>();
  @Output() readonly pay = new EventEmitter<LoanEMI>();

  statusLabel(emi: LoanEMI): string {
    if (emi.status === 'PAID') return 'Paid';
    if (emi.status === 'CANCELLED') return 'Cancelled';
    return 'Pending';
  }

  money(amount: number | null | undefined): string {
    return this.currency.format(amount);
  }
}
