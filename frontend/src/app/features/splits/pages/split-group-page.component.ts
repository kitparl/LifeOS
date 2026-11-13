import { DatePipe } from '@angular/common';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { Observable, forkJoin, of, switchMap } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { apiErrorMessage } from '../../../core/utils/http';
import { AddSplitSubmit, SplitAddFormComponent } from '../components/add-split-form.component';
import { MarkPaidRequest, SplitSettleListComponent } from '../components/settle-list.component';
import { SplitPersonComponent } from '../components/person.component';
import { SplitPrivacyNoteComponent } from '../components/privacy-note.component';
import { ShareActionsComponent } from '../../../shared/share/share-actions.component';
import { SPLIT_SHARE_TEXT } from '../utils/share-links';
import { SplitBalances, SplitExpense, SplitGroupView, SplitMember } from '../models/split.models';
import { SplitDeviceStoreService } from '../services/split-device-store.service';
import { SplitsApiService } from '../services/splits-api.service';
import { linkStatusLabel } from '../utils/link-status';
import { billImpactPaise, isEqualSplit } from '../utils/bill-impact';
import { formatInr } from '../utils/money';

const CLOCK_TICK_MS = 60_000;

type GroupTab = 'bills' | 'balances';

interface BillImpact {
  label: string;
  color: string;
}

/**
 * Public group page (`/s/:code`). Guests and signed-in users open the same URL and
 * see the same group; the seat secret saved on this device decides what they can do.
 */
@Component({
  selector: 'app-split-group-page',
  standalone: true,
  imports: [
    DatePipe,
    LucideDynamicIcon,
    RouterLink,
    SplitAddFormComponent,
    SplitPersonComponent,
    SplitPrivacyNoteComponent,
    SplitSettleListComponent,
    ShareActionsComponent,
  ],
  template: `
    <!-- The app root is a fixed 100dvh box with overflow hidden, so this page scrolls itself. -->
    <div class="h-dvh overflow-y-auto" style="background: var(--page-bg); color: var(--text)" data-testid="split-page-scroll">
      <header
        class="sticky top-0 z-10 flex items-center justify-between gap-2 px-4 py-2"
        style="background: var(--sidebar-bg); border-bottom: 1px solid var(--border)"
      >
        <a class="text-sm font-semibold" [routerLink]="homeLink()">LifeOS · Split bills</a>
        @if (!auth.isAuthenticated()) {
          <a class="btn-ghost text-xs" routerLink="/login">Sign in</a>
        }
      </header>

      <main class="mx-auto max-w-2xl space-y-3 p-4 pb-12">
        @if (error()) {
          <p class="rounded-lg p-3 text-sm" style="background: var(--danger-soft); color: var(--danger)">{{ error() }}</p>
        }

        @if (group(); as g) {
          <!-- Group header and invite -->
          <section class="panel space-y-3" data-testid="split-group-header">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <h1 class="truncate text-lg font-semibold">{{ g.name }}</h1>
                <p class="text-xs" style="color: var(--text-muted)">
                  {{ g.members.length }} {{ g.members.length === 1 ? 'person' : 'people' }} · {{ money(totalPaise()) }} spent
                </p>
              </div>
              <span class="chip shrink-0 text-xs" data-testid="split-link-status">{{ status() }}</span>
            </div>

            <ul class="flex flex-wrap gap-2" data-testid="split-members">
              @for (m of g.members; track m.id) {
                <li class="rounded-full border border-[var(--xp-border)] py-1 pl-1 pr-2 text-sm">
                  <app-split-person [name]="m.display_name" [you]="m.id === g.my_member_id" size="md" />
                </li>
              }
            </ul>

            <details class="border-t border-[var(--xp-border)] pt-3" [open]="g.members.length === 1">
              <summary class="flex cursor-pointer select-none items-center gap-2 text-sm font-medium">
                <svg class="h-4 w-4" lucideIcon="users" aria-hidden="true"></svg>
                Invite people
              </summary>
              <div class="pt-3">
                <app-share-actions [name]="g.name" [urlPath]="g.url_path" [text]="shareText" testIdPrefix="split" />
              </div>
            </details>

            @if (canKeep() || (g.is_creator && g.is_open)) {
              <div class="flex flex-wrap items-center gap-2 text-xs">
                @if (canKeep()) {
                  <button type="button" class="btn-secondary text-xs" data-testid="split-keep" [disabled]="busy()" (click)="keep()">
                    Keep in my history
                  </button>
                }
                @if (g.is_creator && g.is_open) {
                  @if (confirmEnd()) {
                    <span>End the link? Nobody can join or add bills after this.</span>
                    <button type="button" class="btn-danger text-xs" data-testid="split-end" [disabled]="busy()" (click)="end()">
                      End now
                    </button>
                    <button type="button" class="btn-ghost text-xs" (click)="confirmEnd.set(false)">Cancel</button>
                  } @else {
                    <button type="button" class="btn-ghost text-xs" data-testid="split-end-start" (click)="confirmEnd.set(true)">
                      End session
                    </button>
                  }
                }
              </div>
            }
          </section>

          <!-- My balance -->
          @if (g.my_member_id && balances()) {
            <section
              class="panel space-y-3"
              data-testid="split-my-balance"
              [style.border-color]="myNetPaise() > 0 ? 'var(--success)' : myNetPaise() < 0 ? 'var(--danger)' : 'var(--border)'"
            >
              <div class="flex items-center gap-3">
                <span
                  class="grid h-11 w-11 shrink-0 place-items-center rounded-full"
                  [style.background]="myNetPaise() > 0 ? 'var(--success-soft)' : myNetPaise() < 0 ? 'var(--danger-soft)' : 'var(--surface-2)'"
                  [style.color]="myNetPaise() > 0 ? 'var(--success)' : myNetPaise() < 0 ? 'var(--danger)' : 'var(--text-muted)'"
                >
                  <svg class="h-5 w-5" [lucideIcon]="myNetPaise() === 0 ? 'circle-check' : 'wallet'" aria-hidden="true"></svg>
                </span>
                <div class="min-w-0">
                  <p class="text-xs" style="color: var(--text-muted)">{{ myNetPaise() > 0 ? 'You are owed' : myNetPaise() < 0 ? 'You owe' : 'Your balance' }}</p>
                  <p
                    class="text-2xl font-semibold tabular-nums"
                    [style.color]="myNetPaise() > 0 ? 'var(--success)' : myNetPaise() < 0 ? 'var(--danger)' : 'var(--text)'"
                    data-testid="split-my-net"
                  >{{ myNetPaise() === 0 ? 'All settled up' : money(abs(myNetPaise())) }}</p>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div class="rounded p-2" style="background: var(--surface-2)">
                  <p style="color: var(--text-muted)">You paid</p>
                  <p class="text-sm font-semibold tabular-nums">{{ money(myPaidPaise()) }}</p>
                </div>
                <div class="rounded p-2" style="background: var(--surface-2)">
                  <p style="color: var(--text-muted)">Your share</p>
                  <p class="text-sm font-semibold tabular-nums">{{ money(mySharePaise()) }}</p>
                </div>
              </div>
              @if (myNetPaise() !== 0 && tab() !== 'balances') {
                <button type="button" class="btn-primary w-full text-sm" data-testid="split-settle-up" (click)="tab.set('balances')">
                  {{ myNetPaise() < 0 ? 'Settle up' : 'See who owes you' }}
                </button>
              }
            </section>
          }

          <div class="tab-bar" role="tablist" aria-label="Group sections">
            <button
              type="button"
              role="tab"
              class="tab-bar__btn"
              data-testid="split-tab-bills"
              [class.active]="tab() === 'bills'"
              [attr.aria-selected]="tab() === 'bills'"
              (click)="tab.set('bills')"
            >Bills ({{ g.expenses.length }})</button>
            <button
              type="button"
              role="tab"
              class="tab-bar__btn"
              data-testid="split-tab-balances"
              [class.active]="tab() === 'balances'"
              [attr.aria-selected]="tab() === 'balances'"
              (click)="tab.set('balances')"
            >Balances</button>
          </div>

          @if (tab() === 'bills') {
            <section class="panel space-y-3">
              @if (!g.my_member_id) {
                @if (g.is_open) {
                  <form class="space-y-2 text-sm" (submit)="$event.preventDefault(); join()">
                    <label class="block text-xs" for="split-join-name">Join to add your bills — just enter your name</label>
                    <div class="flex gap-2">
                      <input
                        id="split-join-name"
                        class="input-field min-w-0 flex-1"
                        maxlength="40"
                        placeholder="Your name"
                        data-testid="split-join-name"
                        [value]="joinName()"
                        (input)="joinName.set(inputValue($event))"
                      />
                      <button
                        type="submit"
                        class="btn-primary text-xs"
                        data-testid="split-join"
                        [disabled]="!joinName().trim() || busy()"
                      >Join</button>
                    </div>
                  </form>
                } @else {
                  <p class="text-xs" style="color: var(--text-muted)">This link is closed. You can still read the group.</p>
                }
              } @else if (g.is_open) {
                @if (addOpen()) {
                  <app-split-add-form
                    [members]="g.members"
                    [myMemberId]="g.my_member_id"
                    [busy]="busy()"
                    (save)="addSplit($event)"
                    (closed)="addOpen.set(false)"
                  />
                } @else {
                  <button
                    type="button"
                    class="btn-primary inline-flex w-full items-center justify-center gap-2 text-sm"
                    data-testid="split-add"
                    (click)="addOpen.set(true)"
                  >
                    <svg class="h-4 w-4" lucideIcon="plus" aria-hidden="true"></svg>
                    Add bill
                  </button>
                }
              }

              @if (g.expenses.length) {
                <ul class="divide-y divide-[var(--xp-border)] text-sm" data-testid="split-bills">
                  @for (e of newestFirst(); track e.id) {
                    <li class="py-3" data-testid="split-bill-row">
                      <div class="flex items-start gap-3">
                        <div
                          class="grid w-10 shrink-0 place-items-center rounded py-1 text-center leading-tight"
                          style="background: var(--surface-2); color: var(--text-muted)"
                        >
                          <span class="text-[10px] uppercase">{{ e.expense_date | date: 'MMM' }}</span>
                          <span class="text-base font-semibold" style="color: var(--text)">{{ e.expense_date | date: 'dd' }}</span>
                        </div>
                        <div class="min-w-0 flex-1">
                          <div class="flex items-baseline justify-between gap-2">
                            <p class="min-w-0 truncate font-medium">{{ e.title }}</p>
                            <span class="shrink-0 font-semibold tabular-nums">{{ money(e.amount_paise) }}</span>
                          </div>
                          <p class="mt-0.5 flex flex-wrap items-center gap-1 text-xs" style="color: var(--text-muted)">
                            <app-split-person [name]="memberName(e.paid_by)" [you]="e.paid_by === g.my_member_id" />
                            paid · {{ splitLabel(e) }}
                          </p>
                          <div class="mt-1 flex items-center justify-between gap-2">
                            @if (impact(e); as i) {
                              <span class="text-xs font-medium" [style.color]="i.color" data-testid="split-bill-impact">{{ i.label }}</span>
                            } @else {
                              <span></span>
                            }
                            @if (canDelete(e)) {
                              @if (confirmDelete() === e.id) {
                                <span class="flex items-center gap-2 text-xs">
                                  Delete this bill?
                                  <button type="button" class="btn-danger text-xs" data-testid="split-bill-delete-confirm" [disabled]="busy()" (click)="deleteBill(e.id)">
                                    Delete
                                  </button>
                                  <button type="button" class="btn-ghost text-xs" (click)="confirmDelete.set(null)">Cancel</button>
                                </span>
                              } @else {
                                <button
                                  type="button"
                                  class="btn-ghost !min-h-auto !p-1"
                                  data-testid="split-bill-delete"
                                  [attr.aria-label]="'Delete ' + e.title"
                                  (click)="confirmDelete.set(e.id)"
                                >
                                  <svg class="h-4 w-4" lucideIcon="trash-2" aria-hidden="true"></svg>
                                </button>
                              }
                            }
                          </div>
                        </div>
                      </div>
                    </li>
                  }
                </ul>
              } @else if (g.members.length === 1) {
                <p class="text-xs" style="color: var(--text-muted)">Share the link. People join only if they want to.</p>
              } @else {
                <p class="flex items-center gap-2 text-xs" style="color: var(--text-muted)">
                  <svg class="h-4 w-4" lucideIcon="receipt" aria-hidden="true"></svg>
                  No bills yet.
                </p>
              }
            </section>
          } @else {
            @if (balances(); as b) {
              <section class="panel space-y-3">
                <h2 class="text-sm font-semibold">Settle up</h2>
                <app-split-settle-list
                  [debts]="b.debts"
                  [members]="g.members"
                  [settlements]="g.settlements"
                  [myMemberId]="g.my_member_id"
                  [linkOpen]="g.is_open"
                  [busy]="busy()"
                  (markPaid)="markPaid($event)"
                  (confirm)="confirmPayment($event)"
                  (saveUpi)="saveUpi($event)"
                />
              </section>

              <section class="panel space-y-2">
                <h2 class="text-sm font-semibold">Everyone's balance</h2>
                <ul class="divide-y divide-[var(--xp-border)] text-sm">
                  @for (n of b.nets; track n.member_id) {
                    <li class="flex items-center justify-between gap-2 py-2" data-testid="split-net-row">
                      <app-split-person [name]="n.display_name" [you]="n.member_id === g.my_member_id" size="md" />
                      <span
                        class="shrink-0 text-xs font-medium tabular-nums"
                        [style.color]="n.net_paise > 0 ? 'var(--success)' : n.net_paise < 0 ? 'var(--danger)' : 'var(--text-muted)'"
                      >{{ netLabel(n.net_paise) }}</span>
                    </li>
                  }
                </ul>
              </section>
            }
          }

          <app-split-privacy-note />
        } @else if (loading()) {
          <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
        }
      </main>
    </div>
  `,
})
export class SplitGroupPageComponent implements OnInit {
  readonly shareText = SPLIT_SHARE_TEXT;
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(SplitsApiService);
  private readonly store = inject(SplitDeviceStoreService);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly auth = inject(AuthService);

  readonly group = signal<SplitGroupView | null>(null);
  readonly balances = signal<SplitBalances | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly busy = signal(false);
  readonly joinName = signal('');
  readonly addOpen = signal(false);
  readonly confirmEnd = signal(false);
  readonly tab = signal<GroupTab>('bills');
  /** The bill whose delete prompt is open. */
  readonly confirmDelete = signal<string | null>(null);
  private readonly now = signal(Date.now());

  readonly code = this.route.snapshot.paramMap.get('code') ?? '';
  /** This device's seat for the group, if it created or joined it. */
  private readonly seat = signal<string | null>(this.store.find(this.code)?.seatSecret ?? null);

  readonly status = computed(() => {
    const g = this.group();
    return g ? linkStatusLabel(g, this.now()) : '';
  });
  /** Signed in, holding a seat here, and the group is not in this account's history yet. */
  readonly canKeep = computed(() => {
    const g = this.group();
    return this.auth.isAuthenticated() && !!g?.my_member_id && g.in_history === false;
  });
  readonly homeLink = computed(() => (this.auth.isAuthenticated() ? '/splits' : '/explore/splits'));
  readonly newestFirst = computed(() => [...(this.group()?.expenses ?? [])].reverse());
  readonly totalPaise = computed(() => (this.group()?.expenses ?? []).reduce((sum, e) => sum + e.amount_paise, 0));
  readonly myNetPaise = computed(() => {
    const me = this.group()?.my_member_id;
    return this.balances()?.nets.find((n) => n.member_id === me)?.net_paise ?? 0;
  });
  readonly myPaidPaise = computed(() => {
    const me = this.group()?.my_member_id;
    return (this.group()?.expenses ?? []).filter((e) => e.paid_by === me).reduce((sum, e) => sum + e.amount_paise, 0);
  });
  readonly mySharePaise = computed(() => {
    const me = this.group()?.my_member_id;
    return (this.group()?.expenses ?? [])
      .flatMap((e) => e.shares)
      .filter((s) => s.member_id === me)
      .reduce((sum, s) => sum + s.amount_paise, 0);
  });
  private readonly membersById = computed(
    () => new Map<string, SplitMember>((this.group()?.members ?? []).map((m) => [m.id, m])),
  );

  ngOnInit(): void {
    const timer = setInterval(() => this.now.set(Date.now()), CLOCK_TICK_MS);
    this.destroyRef.onDestroy(() => clearInterval(timer));
    this.load();
  }

  load(): void {
    forkJoin([this.api.getGroup(this.code, this.seat()), this.api.getBalances(this.code)]).subscribe({
      next: ([group, balances]) => {
        this.group.set(group);
        this.balances.set(balances);
        this.error.set(null);
        this.loading.set(false);
      },
      error: (err: unknown) => {
        this.error.set(apiErrorMessage(err, 'Could not load this group.'));
        this.loading.set(false);
      },
    });
  }

  join(): void {
    const group = this.group();
    const displayName = this.joinName().trim();
    if (!group || !displayName) return;
    this.run(this.api.joinGroup(this.code, { display_name: displayName }), 'Could not join.', (seat) => {
      this.store.save({
        code: this.code,
        name: group.name,
        seatSecret: seat.seat_secret,
        displayName,
        role: 'member',
      });
      this.seat.set(seat.seat_secret);
    });
  }

  addSplit({ expense, upiVpa }: AddSplitSubmit): void {
    const seat = this.seat();
    if (!seat) return;
    const saveUpi: Observable<unknown> = upiVpa ? this.api.updateMe(this.code, seat, { upi_vpa: upiVpa }) : of(null);
    const request = saveUpi.pipe(switchMap(() => this.api.addExpense(this.code, seat, expense)));
    this.run(request, 'Could not save the bill.', () => this.addOpen.set(false));
  }

  markPaid({ debt, method }: MarkPaidRequest): void {
    const seat = this.seat();
    if (!seat) return;
    const payload = { payee_member_id: debt.payee_member_id, amount_rupees: debt.amount_paise / 100, method };
    this.run(this.api.markPaid(this.code, seat, payload), 'Could not mark as paid.', () => undefined);
  }

  confirmPayment(settlementId: string): void {
    const seat = this.seat();
    if (!seat) return;
    this.run(this.api.confirmSettlement(settlementId, seat), 'Could not confirm.', () => undefined);
  }

  saveUpi(upiVpa: string | null): void {
    const seat = this.seat();
    if (!seat) return;
    this.run(this.api.updateMe(this.code, seat, { upi_vpa: upiVpa }), 'Could not save your UPI id.', () => undefined);
  }

  deleteBill(expenseId: string): void {
    const seat = this.seat();
    if (!seat) return;
    this.run(this.api.deleteExpense(this.code, seat, expenseId), 'Could not delete the bill.', () =>
      this.confirmDelete.set(null),
    );
  }

  end(): void {
    const seat = this.seat();
    if (!seat) return;
    this.run(this.api.endGroup(this.code, seat), 'Could not end the link.', () => this.confirmEnd.set(false));
  }

  keep(): void {
    const seat = this.seat();
    if (!seat) return;
    this.run(this.api.keepInHistory(this.code, seat), 'Could not save to your history.', () => undefined);
  }

  inputValue(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  /** Runs a mutation, then reloads the group from the server (the source of truth). */
  private run<T>(request: Observable<T>, failure: string, onSuccess: (result: T) => void): void {
    this.busy.set(true);
    request.subscribe({
      next: (result) => {
        onSuccess(result);
        this.busy.set(false);
        this.load();
      },
      error: (err: unknown) => {
        this.error.set(apiErrorMessage(err, failure));
        this.busy.set(false);
      },
    });
  }

  memberName(id: string): string {
    return this.membersById().get(id)?.display_name ?? 'Someone';
  }

  /** Only whoever added a bill, or the group creator, may delete it while the link is open. */
  canDelete(expense: SplitExpense): boolean {
    const g = this.group();
    return !!g?.is_open && !!g.my_member_id && (expense.created_by === g.my_member_id || g.is_creator);
  }

  splitLabel(expense: SplitExpense): string {
    const people = expense.shares.length === 1 ? '1 person' : `${expense.shares.length} people`;
    return `${isEqualSplit(expense) ? 'split equally' : 'split unequally'} · ${people}`;
  }

  /** "you lent ₹600" / "you borrowed ₹300" from the viewer's seat; null for visitors. */
  impact(expense: SplitExpense): BillImpact | null {
    const me = this.group()?.my_member_id;
    if (!me) return null;
    const paise = billImpactPaise(expense, me);
    if (paise === null) return { label: 'not involved', color: 'var(--text-faint)' };
    if (paise > 0) return { label: `you lent ${formatInr(paise)}`, color: 'var(--success)' };
    if (paise < 0) return { label: `you borrowed ${formatInr(-paise)}`, color: 'var(--danger)' };
    return { label: 'just you', color: 'var(--text-muted)' };
  }

  netLabel(netPaise: number): string {
    if (netPaise === 0) return 'settled up';
    return netPaise > 0 ? `gets back ${formatInr(netPaise)}` : `owes ${formatInr(-netPaise)}`;
  }

  abs(value: number): number {
    return Math.abs(value);
  }

  money(paise: number): string {
    return formatInr(paise);
  }
}
