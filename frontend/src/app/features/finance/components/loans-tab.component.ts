import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output, inject, signal } from '@angular/core';
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
              <span class="text-xs">{{ statusLabelFor(loan) }}</span>
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

            <div class="flex flex-wrap items-center gap-2 border-t border-[var(--xp-border)] px-3 py-2">
              <button type="button" class="btn-secondary text-xs" (click)="toggleSchedule.emit(loan)">
                {{ expandedLoanId === loan.id ? 'Hide schedule' : 'View schedule' }}
              </button>
              <button type="button" class="btn-secondary text-xs" (click)="edit.emit(loan)">Edit</button>
              <button type="button" class="btn-secondary text-xs" (click)="toggleMenu(loan.id)">
                {{ openMenuLoanId() === loan.id ? 'Close' : 'More ⋮' }}
              </button>
            </div>

            @if (openMenuLoanId() === loan.id) {
              <div class="flex flex-wrap gap-2 border-t border-[var(--xp-border)] px-3 py-2 text-xs">
                @if (loan.status === 'ACTIVE') {
                  <button type="button" class="btn-secondary text-xs" (click)="choose(partPayment, loan)">
                    Make Part Payment
                  </button>
                  <button type="button" class="btn-secondary text-xs" (click)="choose(foreclose, loan)">
                    Foreclose Loan
                  </button>
                }
                @if (loan.status === 'FORECLOSED') {
                  <button type="button" class="btn-secondary text-xs" (click)="choose(reactivate, loan)">
                    Reactivate
                  </button>
                }
                <button
                  type="button"
                  class="btn-secondary text-xs"
                  style="color: var(--danger)"
                  (click)="choose(deleteLoan, loan)"
                >
                  Delete Loan
                </button>
              </div>
            }

            @if (loan.status === 'FORECLOSED' && loan.foreclosure_amount !== null) {
              <p class="border-t border-[var(--xp-border)] px-3 py-2 text-xs" style="color: var(--text-muted)">
                Foreclosed {{ loan.foreclosed_at | date: 'dd MMM yyyy' }} · {{ money(loan.foreclosure_amount) }}
              </p>
            }

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
  @Output() readonly partPayment = new EventEmitter<Loan>();
  @Output() readonly foreclose = new EventEmitter<Loan>();
  @Output() readonly reactivate = new EventEmitter<Loan>();
  @Output() readonly deleteLoan = new EventEmitter<Loan>();
  @Output() readonly toggleSchedule = new EventEmitter<Loan>();
  @Output() readonly pay = new EventEmitter<LoanEMI>();

  readonly openMenuLoanId = signal<string | null>(null);

  toggleMenu(loanId: string): void {
    this.openMenuLoanId.set(this.openMenuLoanId() === loanId ? null : loanId);
  }

  choose(emitter: EventEmitter<Loan>, loan: Loan): void {
    this.openMenuLoanId.set(null);
    emitter.emit(loan);
  }

  statusLabelFor(loan: Loan): string {
    if (loan.status === 'COMPLETED') return 'Completed';
    if (loan.status === 'FORECLOSED') return 'Foreclosed';
    return 'Active';
  }

  statusLabel(emi: LoanEMI): string {
    if (emi.status === 'PAID') return 'Paid';
    if (emi.status === 'CANCELLED') return 'Cancelled';
    return 'Upcoming';
  }

  money(amount: number | null | undefined): string {
    return this.currency.format(amount);
  }
}
