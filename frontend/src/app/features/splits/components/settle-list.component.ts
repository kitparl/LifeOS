import { Component, HostListener, computed, inject, input, output, signal } from '@angular/core';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { QrCodeComponent } from '../../../shared/qr-code/qr-code.component';
import {
  SplitDebt,
  SplitMember,
  SplitSettlement,
  SplitSettlementMethod,
  UPI_VPA_PATTERN,
} from '../models/split.models';
import { formatInr } from '../utils/money';

const UPI_INTENT_PREFIX = 'upi://pay?';

export interface MarkPaidRequest {
  debt: SplitDebt;
  method: SplitSettlementMethod;
}

/**
 * Settle: one row per pairwise debt. With a payee UPI id the row has a Pay link and a
 * payment QR, both the same `upi://` intent for the price; without one it is cash only.
 * The payer marks paid; the payee confirms. LifeOS never sees the money move.
 */
@Component({
  selector: 'app-split-settle-list',
  standalone: true,
  imports: [QrCodeComponent],
  template: `
    <div class="space-y-3 text-sm">
      @if (prompt(); as debt) {
        <div class="panel flex flex-wrap items-center justify-between gap-2" data-testid="split-paid-prompt">
          <p>Mark {{ money(debt.amount_paise) }} to {{ debt.payee_name }} as paid?</p>
          <div class="flex gap-2">
            <button type="button" class="btn-primary text-xs" (click)="answerPrompt(true)">Yes, mark paid</button>
            <button type="button" class="btn-ghost text-xs" (click)="answerPrompt(false)">Not yet</button>
          </div>
        </div>
      }

      @if (debts().length) {
        <ul class="divide-y divide-[var(--xp-border)]" data-testid="split-debts">
          @for (debt of debts(); track debt.payer_member_id + debt.payee_member_id) {
            <li class="space-y-2 py-2" data-testid="split-debt-row">
              <p>
                <span class="font-medium">{{ debt.payer_name }}</span> owes
                <span class="font-medium">{{ debt.payee_name }}</span>
                {{ money(debt.outstanding_paise) }}
              </p>
              @if (debt.pending_paise > 0) {
                <p class="text-xs" style="color: var(--text-muted)">
                  {{ money(debt.pending_paise) }} marked paid, awaiting {{ debt.payee_name }}
                </p>
              }
              @if (debt.amount_paise > 0) {
                @if (debt.upi_uri) {
                  <div class="flex flex-wrap items-start gap-3">
                    <div class="inline-block rounded border border-[var(--xp-border)] bg-white p-1" data-testid="split-payment-qr">
                      <app-qr-code [payload]="debt.upi_uri" [size]="136" [label]="'UPI payment QR for ' + debt.payee_name" />
                    </div>
                    <div class="flex flex-col gap-2">
                      <a class="btn-primary text-xs" data-testid="split-pay" [href]="payHref(debt.upi_uri)" (click)="onPay(debt)">
                        Pay {{ money(debt.amount_paise) }}
                      </a>
                      @if (debt.payer_member_id === myMemberId()) {
                        <button type="button" class="btn-secondary text-xs" data-testid="split-mark-paid" [disabled]="busy()" (click)="markPaid.emit({ debt, method: 'upi' })">
                          Mark paid
                        </button>
                      }
                    </div>
                  </div>
                } @else {
                  <p class="text-xs" style="color: var(--text-muted)">Add a UPI id to get a pay link and QR.</p>
                  @if (debt.payer_member_id === myMemberId()) {
                    <button type="button" class="btn-secondary text-xs" data-testid="split-mark-paid" [disabled]="busy()" (click)="markPaid.emit({ debt, method: 'cash' })">
                      Mark as cash
                    </button>
                  }
                }
              }
            </li>
          }
        </ul>
      } @else {
        <p style="color: var(--text-muted)">Everyone is settled up.</p>
      }

      @if (toConfirm().length) {
        <div class="space-y-1">
          <h3 class="text-xs font-semibold">Waiting for you to confirm</h3>
          @for (s of toConfirm(); track s.id) {
            <div class="flex items-center justify-between gap-2">
              <span>{{ nameOf(s.payer_member_id) }} paid you {{ money(s.amount_paise) }} ({{ s.method === 'upi' ? 'UPI' : 'cash' }})</span>
              <button type="button" class="btn-primary text-xs" data-testid="split-confirm" [disabled]="busy()" (click)="confirm.emit(s.id)">
                Confirm
              </button>
            </div>
          }
        </div>
      }

      @if (me(); as m) {
        <form class="flex flex-wrap items-end gap-2" (submit)="$event.preventDefault(); submitUpi()">
          <div class="min-w-0 flex-1">
            <label class="mb-1 block text-xs" for="split-my-upi">Your UPI id</label>
            <input
              id="split-my-upi"
              class="input-field"
              placeholder="name@bank"
              maxlength="129"
              data-testid="split-my-upi"
              [value]="upiDraft() ?? m.upi_vpa ?? ''"
              (input)="upiDraft.set(inputValue($event))"
            />
          </div>
          <button type="submit" class="btn-secondary text-xs" data-testid="split-upi-save" [disabled]="!upiValid() || busy()">
            Save
          </button>
        </form>
      }
    </div>
  `,
})
export class SplitSettleListComponent {
  private readonly sanitizer = inject(DomSanitizer);

  readonly debts = input.required<SplitDebt[]>();
  readonly members = input.required<SplitMember[]>();
  readonly settlements = input.required<SplitSettlement[]>();
  readonly myMemberId = input<string | null>(null);
  readonly busy = input(false);

  readonly markPaid = output<MarkPaidRequest>();
  readonly confirm = output<string>();
  readonly saveUpi = output<string | null>();

  /** The debt whose Pay link was tapped; asked about once when the page is visible again. */
  private readonly awaitingReturn = signal<SplitDebt | null>(null);
  readonly prompt = signal<SplitDebt | null>(null);
  readonly upiDraft = signal<string | null>(null);

  readonly me = computed(() => this.members().find((m) => m.id === this.myMemberId()) ?? null);
  readonly toConfirm = computed(() =>
    this.settlements().filter((s) => s.status === 'paid' && s.payee_member_id === this.myMemberId()),
  );
  readonly upiValid = computed(() => {
    const draft = (this.upiDraft() ?? '').trim();
    return this.upiDraft() !== null && (!draft || UPI_VPA_PATTERN.test(draft));
  });

  /** Angular blocks non-web schemes in [href]; only the server-built UPI intent is let through. */
  payHref(uri: string): SafeUrl | null {
    return uri.startsWith(UPI_INTENT_PREFIX) ? this.sanitizer.bypassSecurityTrustUrl(uri) : null;
  }

  onPay(debt: SplitDebt): void {
    if (debt.payer_member_id === this.myMemberId()) this.awaitingReturn.set(debt);
  }

  @HostListener('document:visibilitychange')
  onVisibilityChange(): void {
    const debt = this.awaitingReturn();
    if (debt && document.visibilityState === 'visible') {
      this.awaitingReturn.set(null);
      this.prompt.set(debt);
    }
  }

  answerPrompt(paid: boolean): void {
    const debt = this.prompt();
    this.prompt.set(null);
    if (paid && debt) this.markPaid.emit({ debt, method: 'upi' });
  }

  submitUpi(): void {
    if (!this.upiValid()) return;
    this.saveUpi.emit((this.upiDraft() ?? '').trim() || null);
    this.upiDraft.set(null);
  }

  nameOf(memberId: string): string {
    return this.members().find((m) => m.id === memberId)?.display_name ?? 'Someone';
  }

  inputValue(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  money(paise: number): string {
    return formatInr(paise);
  }
}
