import { Component, HostListener, computed, inject, input, output, signal } from '@angular/core';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { LucideDynamicIcon } from '@lucide/angular';
import { QrCodeComponent } from '../../../shared/qr-code/qr-code.component';
import { SplitPersonComponent } from './person.component';
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
 * Settle: one card per simplified debt, the viewer's own first. With a payee UPI id the row has a Pay link and a
 * payment QR, both the same `upi://` intent for the price; without one it is cash only.
 * The payer marks paid; the payee confirms. LifeOS never sees the money move.
 */
@Component({
  selector: 'app-split-settle-list',
  standalone: true,
  imports: [LucideDynamicIcon, QrCodeComponent, SplitPersonComponent],
  template: `
    <div class="space-y-3 text-sm">
      @if (prompt(); as debt) {
        <div
          class="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3"
          style="border-color: var(--primary); background: var(--primary-soft)"
          data-testid="split-paid-prompt"
        >
          <p>Mark {{ money(debt.amount_paise) }} to {{ debt.payee_name }} as paid?</p>
          <div class="flex gap-2">
            <button type="button" class="btn-primary text-xs" (click)="answerPrompt(true)">Yes, mark paid</button>
            <button type="button" class="btn-ghost text-xs" (click)="answerPrompt(false)">Not yet</button>
          </div>
        </div>
      }

      @if (debts().length) {
        <ul class="space-y-2" data-testid="split-debts">
          @for (debt of sortedDebts(); track debt.payer_member_id + debt.payee_member_id) {
            <li
              class="space-y-3 rounded-lg border p-3"
              data-testid="split-debt-row"
              [style.border-color]="isMine(debt) ? 'var(--primary)' : 'var(--border)'"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="flex min-w-0 flex-wrap items-center gap-1.5">
                  <app-split-person [name]="debt.payer_name" [you]="debt.payer_member_id === myMemberId()" size="md" />
                  <span style="color: var(--text-muted)">pays</span>
                  <app-split-person [name]="debt.payee_name" [you]="debt.payee_member_id === myMemberId()" size="md" />
                </p>
                <span class="shrink-0 text-base font-semibold tabular-nums" [style.color]="amountColor(debt)">
                  {{ money(debt.outstanding_paise) }}
                </span>
              </div>
              @if (debt.pending_paise > 0) {
                <p class="rounded px-2 py-1 text-xs" style="background: var(--warning-soft); color: var(--text)">
                  {{ money(debt.pending_paise) }} marked paid, awaiting {{ debt.payee_name }}
                </p>
              }
              @if (debt.amount_paise > 0) {
                @if (debt.upi_uri) {
                  <div class="flex flex-wrap items-start gap-3">
                    <div class="inline-block rounded border border-[var(--xp-border)] bg-white p-1" data-testid="split-payment-qr">
                      <app-qr-code [payload]="debt.upi_uri" [size]="128" [label]="'UPI payment QR for ' + debt.payee_name" />
                    </div>
                    <div class="flex min-w-[10rem] flex-1 flex-col gap-2">
                      <a class="btn-primary text-center text-sm" data-testid="split-pay" [href]="payHref(debt.upi_uri)" (click)="onPay(debt)">
                        Pay {{ money(debt.amount_paise) }} via UPI
                      </a>
                      @if (debt.payer_member_id === myMemberId()) {
                        <button type="button" class="btn-secondary text-xs" data-testid="split-mark-paid" [disabled]="busy()" (click)="markPaid.emit({ debt, method: 'upi' })">
                          Mark paid
                        </button>
                        <button type="button" class="btn-ghost text-xs" data-testid="split-mark-cash" [disabled]="busy()" (click)="markPaid.emit({ debt, method: 'cash' })">
                          Paid in cash
                        </button>
                      }
                    </div>
                  </div>
                } @else {
                  <p class="text-xs" style="color: var(--text-muted)">
                    {{ linkOpen() ? 'Add a UPI id to get a pay link and QR.' : 'Link closed, so UPI ids are erased. Pay in cash or any app, then mark it.' }}
                  </p>
                  @if (debt.payer_member_id === myMemberId()) {
                    <button type="button" class="btn-secondary w-full text-xs sm:w-auto" data-testid="split-mark-paid" [disabled]="busy()" (click)="markPaid.emit({ debt, method: 'cash' })">
                      Mark as cash
                    </button>
                  }
                }
              }
            </li>
          }
        </ul>
      } @else {
        <p class="flex items-center gap-2 rounded-lg p-3" style="background: var(--success-soft); color: var(--success)">
          <svg class="h-4 w-4" lucideIcon="circle-check" aria-hidden="true"></svg>
          Everyone is settled up.
        </p>
      }

      @if (toConfirm().length) {
        <div class="space-y-2 rounded-lg border p-3" style="border-color: var(--success)">
          <h3 class="text-xs font-semibold">Waiting for you to confirm</h3>
          @for (s of toConfirm(); track s.id) {
            <div class="flex items-center justify-between gap-2">
              <span class="flex flex-wrap items-center gap-1.5">
                <app-split-person [name]="nameOf(s.payer_member_id)" />
                paid you <span class="font-semibold">{{ money(s.amount_paise) }}</span>
                ({{ s.method === 'upi' ? 'UPI' : 'cash' }})
              </span>
              <button type="button" class="btn-primary text-xs" data-testid="split-confirm" [disabled]="busy()" (click)="confirm.emit(s.id)">
                Confirm
              </button>
            </div>
          }
        </div>
      }

      @if (linkOpen() && me(); as m) {
        <details class="text-xs" data-testid="split-payment-settings">
          <summary class="cursor-pointer select-none">Payment settings (UPI){{ m.upi_vpa ? ' · ' + m.upi_vpa : '' }}</summary>
          <form class="mt-2 flex flex-wrap items-end gap-2" (submit)="$event.preventDefault(); submitUpi()">
            <div class="min-w-0 flex-1">
              <label class="mb-1 block text-xs" for="split-my-upi">Your UPI id, so people who owe you get a pay link and QR</label>
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
        </details>
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
  readonly linkOpen = input(true);
  readonly busy = input(false);

  readonly markPaid = output<MarkPaidRequest>();
  readonly confirm = output<string>();
  readonly saveUpi = output<string | null>();

  /** The debt whose Pay link was tapped; asked about once when the page is visible again. */
  private readonly awaitingReturn = signal<SplitDebt | null>(null);
  readonly prompt = signal<SplitDebt | null>(null);
  readonly upiDraft = signal<string | null>(null);

  /** My debts (to pay or to receive) first, otherwise the server's seat order. */
  readonly sortedDebts = computed(() => {
    const debts = this.debts();
    return [...debts.filter((d) => this.isMine(d)), ...debts.filter((d) => !this.isMine(d))];
  });
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

  isMine(debt: SplitDebt): boolean {
    const me = this.myMemberId();
    return !!me && (debt.payer_member_id === me || debt.payee_member_id === me);
  }

  amountColor(debt: SplitDebt): string {
    if (debt.payer_member_id === this.myMemberId()) return 'var(--danger)';
    if (debt.payee_member_id === this.myMemberId()) return 'var(--success)';
    return 'var(--text)';
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
