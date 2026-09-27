import { Component, OnInit, computed, input, output, signal } from '@angular/core';
import { SplitExpensePayload, SplitMember, UPI_VPA_PATTERN } from '../models/split.models';
import { equalSplit } from '../utils/equal-split';
import { formatInr, parseRupees, rupeesToPaise } from '../utils/money';

export interface AddSplitSubmit {
  expense: SplitExpensePayload;
  /** Set when the payer (this seat) typed a UPI id on this form. */
  upiVpa: string | null;
}

/**
 * Add a bill: amount, title, who paid (default me) and who is included (default all).
 * Shows each person's share before save; save stays disabled until the shares sum to the amount.
 */
@Component({
  selector: 'app-split-add-form',
  standalone: true,
  template: `
    <form class="grid gap-3 text-sm" data-testid="split-add-form" (submit)="$event.preventDefault(); submit()">
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block" for="split-amount">Amount (₹)</label>
          <input
            id="split-amount"
            class="input-field"
            inputmode="decimal"
            data-testid="split-amount"
            [value]="amountText()"
            (input)="amountText.set(value($event))"
          />
        </div>
        <div>
          <label class="mb-1 block" for="split-title">Title</label>
          <input
            id="split-title"
            class="input-field"
            maxlength="120"
            placeholder="Dinner"
            data-testid="split-title"
            [value]="title()"
            (input)="title.set(value($event))"
          />
        </div>
      </div>

      <div>
        <label class="mb-1 block" for="split-paid-by">Who paid</label>
        <select id="split-paid-by" class="input-field" data-testid="split-paid-by" (change)="setPayer(value($event))">
          @for (m of members(); track m.id) {
            <option [value]="m.id" [selected]="m.id === paidBy()">
              {{ m.display_name }}{{ m.id === myMemberId() ? ' (me)' : '' }}
            </option>
          }
        </select>
      </div>

      <fieldset class="space-y-1">
        <legend class="mb-1">Split equally between</legend>
        @for (m of members(); track m.id) {
          <label class="flex items-center justify-between gap-2" data-testid="split-member-option">
            <span class="flex items-center gap-2">
              <input type="checkbox" [checked]="included().has(m.id)" (change)="toggle(m.id)" />
              {{ m.display_name }}
            </span>
            <span class="text-xs" style="color: var(--text-muted)" data-testid="split-live-share">
              {{ shares().has(m.id) ? money(shares().get(m.id)!) : '—' }}
            </span>
          </label>
        }
      </fieldset>

      @if (askUpi()) {
        <div>
          <label class="mb-1 block" for="split-upi">Your UPI id (optional)</label>
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
        <p class="text-xs" style="color: var(--text-muted)">{{ hint() }}</p>
      }

      <div class="flex justify-end gap-2">
        <button type="button" class="btn-ghost text-xs" (click)="closed.emit()">Cancel</button>
        <button type="submit" class="btn-primary text-xs" data-testid="split-add-save" [disabled]="!canSave() || busy()">
          Save
        </button>
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
  readonly included = signal<Set<string>>(new Set());
  readonly upi = signal('');

  readonly amountPaise = computed(() => {
    const rupees = parseRupees(this.amountText());
    return rupees === null ? null : rupeesToPaise(rupees);
  });
  /** Included members in join order — the order the server hands out remainder paise. */
  private readonly includedIds = computed(() => this.members().filter((m) => this.included().has(m.id)).map((m) => m.id));
  readonly shares = computed(() => {
    const amount = this.amountPaise();
    return amount === null ? new Map<string, number>() : equalSplit(amount, this.includedIds());
  });
  private readonly sharesTotal = computed(() => [...this.shares().values()].reduce((sum, s) => sum + s, 0));

  readonly askUpi = computed(() => {
    const me = this.members().find((m) => m.id === this.myMemberId());
    return this.paidBy() === this.myMemberId() && !me?.upi_vpa;
  });
  private readonly upiValid = computed(() => !this.upi().trim() || UPI_VPA_PATTERN.test(this.upi().trim()));

  readonly hint = computed(() => {
    if (this.amountText() && this.amountPaise() === null) return 'Enter an amount like 450 or 450.50.';
    if (!this.included().has(this.paidBy())) return 'Whoever paid must be included.';
    if (!this.upiValid()) return 'Enter a UPI id like name@bank, or leave it empty.';
    return '';
  });

  readonly canSave = computed(
    () =>
      this.amountPaise() !== null &&
      this.sharesTotal() === this.amountPaise() &&
      this.title().trim().length > 0 &&
      this.included().has(this.paidBy()) &&
      this.upiValid(),
  );

  ngOnInit(): void {
    // Defaults: I paid, split across everyone who has joined.
    this.paidBy.set(this.myMemberId());
    this.included.set(new Set(this.members().map((m) => m.id)));
  }

  value(event: Event): string {
    return (event.target as HTMLInputElement | HTMLSelectElement).value;
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

  money(paise: number): string {
    return formatInr(paise);
  }

  submit(): void {
    if (!this.canSave()) return;
    const upi = this.askUpi() ? this.upi().trim() : '';
    this.save.emit({
      expense: {
        title: this.title().trim(),
        amount_rupees: parseRupees(this.amountText())!,
        paid_by: this.paidBy(),
        member_ids: this.includedIds(),
      },
      upiVpa: upi || null,
    });
  }
}
