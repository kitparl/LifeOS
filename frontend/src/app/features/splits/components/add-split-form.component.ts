import { Component, OnInit, computed, input, output, signal } from '@angular/core';
import { SplitExpensePayload, SplitMember, SplitMode, UPI_VPA_PATTERN } from '../models/split.models';
import { equalSplit } from '../utils/equal-split';
import { formatInr, parseRupees, rupeesToPaise } from '../utils/money';
import { SplitPersonComponent } from './person.component';

export interface AddSplitSubmit {
  expense: SplitExpensePayload;
  /** Set when the payer (this seat) typed a UPI id on this form. */
  upiVpa: string | null;
}

/**
 * Add a bill: big amount, what it was for, who paid (default me), then split it equally between
 * the people ticked (default everyone) or unequally by typing each person's amount. The payer may
 * be left out (paying for someone else). Save stays disabled until the shares add up to the bill.
 */
@Component({
  selector: 'app-split-add-form',
  standalone: true,
  imports: [SplitPersonComponent],
  template: `
    <form class="space-y-4 text-sm" data-testid="split-add-form" (submit)="$event.preventDefault(); submit()">
      <div class="space-y-2 text-center">
        <label class="block text-xs font-medium" style="color: var(--text-muted)" for="split-amount">Amount</label>
        <div class="flex items-baseline justify-center gap-1">
          <span class="text-2xl font-semibold" style="color: var(--text-muted)">₹</span>
          <input
            id="split-amount"
            class="w-44 border-0 border-b-2 bg-transparent text-center text-3xl font-semibold outline-none"
            style="border-color: var(--primary); color: var(--text)"
            inputmode="decimal"
            placeholder="0"
            autocomplete="off"
            data-testid="split-amount"
            [value]="amountText()"
            (input)="amountText.set(value($event))"
          />
        </div>
        <input
          id="split-title"
          class="input-field mx-auto max-w-xs text-center"
          maxlength="120"
          placeholder="What was it for? e.g. Dinner"
          aria-label="What was it for"
          data-testid="split-title"
          [value]="title()"
          (input)="title.set(value($event))"
        />
      </div>

      <div>
        <p class="mb-1.5 text-xs font-medium" style="color: var(--text-muted)">Paid by</p>
        <div class="flex flex-wrap gap-2" role="radiogroup" aria-label="Paid by" data-testid="split-paid-by">
          @for (m of members(); track m.id) {
            <button
              type="button"
              role="radio"
              class="rounded-full border py-1 pl-1 pr-2.5"
              data-testid="split-payer-option"
              [attr.aria-checked]="m.id === paidBy()"
              [style.border-color]="m.id === paidBy() ? 'var(--primary)' : 'var(--border)'"
              [style.background]="m.id === paidBy() ? 'var(--primary-soft)' : 'transparent'"
              (click)="setPayer(m.id)"
            >
              <app-split-person [name]="m.display_name" [you]="m.id === myMemberId()" />
            </button>
          }
        </div>
      </div>

      <div class="space-y-2">
        <div class="tab-bar" role="tablist" aria-label="How to split">
          <button
            type="button"
            role="tab"
            class="tab-bar__btn"
            data-testid="split-mode-equal"
            [class.active]="mode() === 'equal'"
            [attr.aria-selected]="mode() === 'equal'"
            (click)="mode.set('equal')"
          >Equally</button>
          <button
            type="button"
            role="tab"
            class="tab-bar__btn"
            data-testid="split-mode-exact"
            [class.active]="mode() === 'exact'"
            [attr.aria-selected]="mode() === 'exact'"
            (click)="startExact()"
          >Unequally</button>
        </div>

        <ul class="divide-y divide-[var(--xp-border)]">
          @for (m of members(); track m.id) {
            <li class="flex min-h-11 items-center justify-between gap-3 py-1.5" data-testid="split-member-option">
              @if (mode() === 'equal') {
                <label class="flex min-w-0 flex-1 cursor-pointer items-center gap-2">
                  <input type="checkbox" class="h-4 w-4 shrink-0" [checked]="included().has(m.id)" (change)="toggle(m.id)" />
                  <app-split-person [name]="m.display_name" [you]="m.id === myMemberId()" size="md" />
                </label>
                <span
                  class="shrink-0 text-sm tabular-nums"
                  [style.color]="shares().has(m.id) ? 'var(--text)' : 'var(--text-faint)'"
                  data-testid="split-live-share"
                >{{ shares().has(m.id) ? money(shares().get(m.id)!) : '—' }}</span>
              } @else {
                <app-split-person [name]="m.display_name" [you]="m.id === myMemberId()" size="md" />
                <span class="flex shrink-0 items-center gap-1">
                  <span style="color: var(--text-muted)">₹</span>
                  <input
                    class="input-field !w-24 text-right tabular-nums"
                    inputmode="decimal"
                    placeholder="0"
                    data-testid="split-exact-input"
                    [attr.aria-label]="m.display_name + ' pays'"
                    [value]="exactText().get(m.id) ?? ''"
                    (input)="setExact(m.id, value($event))"
                  />
                </span>
              }
            </li>
          }
        </ul>

        @if (amountPaise() !== null) {
          <p class="flex justify-between text-xs" data-testid="split-remaining" [style.color]="remainingColor()">
            <span>{{ money(assignedPaise()) }} of {{ money(amountPaise()!) }}</span>
            <span>{{ remainingLabel() }}</span>
          </p>
        }
      </div>

      @if (askUpi()) {
        <div>
          <label class="mb-1 block text-xs font-medium" for="split-upi">Your UPI id (optional)</label>
          <input
            id="split-upi"
            class="input-field"
            placeholder="name@bank"
            maxlength="129"
            data-testid="split-upi-input"
            [value]="upi()"
            (input)="upi.set(value($event))"
          />
          <p class="mt-1 text-xs" style="color: var(--text-muted)">
            People who owe you get a pay link and QR for it. It is erased when the link closes.
          </p>
        </div>
      }

      @if (hint()) {
        <p class="text-xs" style="color: var(--danger)" data-testid="split-add-hint">{{ hint() }}</p>
      }

      <div class="flex gap-2">
        <button type="button" class="btn-ghost flex-1 text-sm sm:flex-none" (click)="closed.emit()">Cancel</button>
        <button
          type="submit"
          class="btn-primary flex-1 text-sm sm:ml-auto sm:flex-none"
          data-testid="split-add-save"
          [disabled]="!canSave() || busy()"
        >Save bill</button>
      </div>
    </form>
  `,
})
export class SplitAddFormComponent implements OnInit {
  readonly members = input.required<SplitMember[]>();
  readonly myMemberId = input.required<string>();
  readonly busy = input(false);

  readonly save = output<AddSplitSubmit>();
  readonly closed = output<void>();

  readonly amountText = signal('');
  readonly title = signal('');
  readonly paidBy = signal('');
  readonly mode = signal<SplitMode>('equal');
  readonly included = signal<Set<string>>(new Set());
  /** Unequal mode: what was typed per member; blank means not on the bill. */
  readonly exactText = signal<Map<string, string>>(new Map());
  readonly upi = signal('');

  readonly amountPaise = computed(() => {
    const rupees = parseRupees(this.amountText());
    return rupees === null ? null : rupeesToPaise(rupees);
  });
  /** Included members in join order — the order the server hands out remainder paise. */
  private readonly includedIds = computed(() => this.members().filter((m) => this.included().has(m.id)).map((m) => m.id));

  /** Typed amounts that are not valid rupees (blank is fine: that person is left off). */
  private readonly badExact = computed(() =>
    [...this.exactText().values()].some((text) => text.trim() !== '' && parseRupees(text) === null),
  );

  /** Each person's share in paise, in join order; only people with a share are present. */
  readonly shares = computed<Map<string, number>>(() => {
    const amount = this.amountPaise();
    if (this.mode() === 'equal') {
      return amount === null ? new Map() : equalSplit(amount, this.includedIds());
    }
    const shares = new Map<string, number>();
    for (const m of this.members()) {
      const rupees = parseRupees(this.exactText().get(m.id) ?? '');
      if (rupees !== null) shares.set(m.id, rupeesToPaise(rupees));
    }
    return shares;
  });
  readonly assignedPaise = computed(() => [...this.shares().values()].reduce((sum, s) => sum + s, 0));
  private readonly remainingPaise = computed(() => (this.amountPaise() ?? 0) - this.assignedPaise());

  readonly remainingLabel = computed(() => {
    const left = this.remainingPaise();
    if (left === 0) return 'All assigned';
    return left > 0 ? `${formatInr(left)} left` : `${formatInr(-left)} over`;
  });
  readonly remainingColor = computed(() => (this.remainingPaise() === 0 ? 'var(--success)' : 'var(--danger)'));

  readonly askUpi = computed(() => {
    const me = this.members().find((m) => m.id === this.myMemberId());
    return this.paidBy() === this.myMemberId() && !me?.upi_vpa;
  });
  private readonly upiValid = computed(() => !this.upi().trim() || UPI_VPA_PATTERN.test(this.upi().trim()));

  readonly hint = computed(() => {
    if (this.amountText() && this.amountPaise() === null) return 'Enter an amount like 450 or 450.50.';
    if (this.mode() === 'equal' && this.included().size === 0) return 'Pick at least one person to split with.';
    if (this.badExact()) return 'Enter amounts like 120 or 120.50.';
    if (!this.upiValid()) return 'Enter a UPI id like name@bank, or leave it empty.';
    return '';
  });

  readonly canSave = computed(
    () =>
      this.amountPaise() !== null &&
      this.shares().size > 0 &&
      this.remainingPaise() === 0 &&
      !this.badExact() &&
      this.title().trim().length > 0 &&
      this.upiValid(),
  );

  ngOnInit(): void {
    // Defaults: I paid, split across everyone who has joined.
    this.paidBy.set(this.myMemberId());
    this.included.set(new Set(this.members().map((m) => m.id)));
  }

  value(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  setPayer(id: string): void {
    this.paidBy.set(id);
  }

  toggle(id: string): void {
    const next = new Set(this.included());
    if (next.has(id)) next.delete(id);
    else next.add(id);
    this.included.set(next);
  }

  /** Switch to unequal, pre-filled with the current equal shares so only the differences need typing. */
  startExact(): void {
    if (this.mode() === 'exact') return;
    const prefill = new Map<string, string>();
    this.shares().forEach((paise, id) => prefill.set(id, (paise / 100).toFixed(2).replace(/\.00$/, '')));
    this.exactText.set(prefill);
    this.mode.set('exact');
  }

  setExact(id: string, text: string): void {
    this.exactText.set(new Map(this.exactText()).set(id, text));
  }

  money(paise: number): string {
    return formatInr(paise);
  }

  submit(): void {
    if (!this.canSave()) return;
    const upi = this.askUpi() ? this.upi().trim() : '';
    const base = { title: this.title().trim(), amount_rupees: parseRupees(this.amountText())!, paid_by: this.paidBy() };
    const expense: SplitExpensePayload =
      this.mode() === 'equal'
        ? { ...base, member_ids: this.includedIds() }
        : { ...base, shares: [...this.shares()].map(([member_id, paise]) => ({ member_id, amount_rupees: paise / 100 })) };
    this.save.emit({ expense, upiVpa: upi || null });
  }
}
