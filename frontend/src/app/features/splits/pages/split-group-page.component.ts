import { DatePipe } from '@angular/common';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Observable, forkJoin, of, switchMap } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { apiErrorMessage } from '../../../core/utils/http';
import { AddSplitSubmit, SplitAddFormComponent } from '../components/add-split-form.component';
import { MarkPaidRequest, SplitSettleListComponent } from '../components/settle-list.component';
import { SplitPrivacyNoteComponent } from '../components/privacy-note.component';
import { SplitShareActionsComponent } from '../components/share-actions.component';
import { SplitBalances, SplitGroupView, SplitMember } from '../models/split.models';
import { SplitDeviceStoreService } from '../services/split-device-store.service';
import { SplitsApiService } from '../services/splits-api.service';
import { linkStatusLabel } from '../utils/link-status';
import { formatInr } from '../utils/money';

const CLOCK_TICK_MS = 60_000;

/**
 * Public group page (`/s/:code`). Guests and signed-in users open the same URL and
 * see the same group; the seat secret saved on this device decides what they can do.
 */
@Component({
  selector: 'app-split-group-page',
  standalone: true,
  imports: [
    DatePipe,
    RouterLink,
    SplitAddFormComponent,
    SplitPrivacyNoteComponent,
    SplitSettleListComponent,
    SplitShareActionsComponent,
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

      <main class="mx-auto max-w-2xl space-y-4 p-4 pb-12">
        @if (error()) {
          <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
        }

        @if (group(); as g) {
          <!-- 1. Invite -->
          <section class="panel space-y-3" data-testid="split-group-header">
            <div class="flex flex-wrap items-baseline justify-between gap-2">
              <h1 class="text-base font-semibold">{{ g.name }}</h1>
              <span class="chip text-xs" data-testid="split-link-status">{{ status() }}</span>
            </div>
            <app-split-share-actions [groupName]="g.name" [urlPath]="g.url_path" />
            <p class="text-xs" style="color: var(--text-muted)" data-testid="split-members">
              {{ g.members.length }} {{ g.members.length === 1 ? 'person' : 'people' }}:
              @for (m of g.members; track m.id; let last = $last) {
                {{ m.display_name }}{{ m.id === g.my_member_id ? ' (you)' : '' }}{{ last ? '' : ', ' }}
              }
            </p>
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

          <!-- 2. Bills -->
          <section class="panel space-y-3">
            <h2 class="text-sm font-semibold">Bills</h2>

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
                <button type="button" class="btn-primary w-full text-sm sm:w-auto" data-testid="split-add" (click)="addOpen.set(true)">
                  + Add bill
                </button>
              }
            }

            @if (g.expenses.length) {
              <ul class="divide-y divide-[var(--xp-border)] text-sm" data-testid="split-bills">
                @for (e of g.expenses; track e.id) {
                  <li class="py-2" data-testid="split-bill-row">
                    <div class="flex items-center justify-between gap-2">
                      <p class="min-w-0 truncate">{{ e.title }}</p>
                      <span class="font-medium">{{ money(e.amount_paise) }}</span>
                    </div>
                    <p class="text-xs" style="color: var(--text-muted)">
                      Paid by {{ memberName(e.paid_by) }} · {{ e.expense_date | date: 'dd MMM' }} · split
                      {{ e.shares.length === 1 ? '1 way' : e.shares.length + ' ways' }}
                    </p>
                  </li>
                }
              </ul>
            } @else if (g.members.length === 1) {
              <p class="text-xs" style="color: var(--text-muted)">Share the link. People join only if they want to.</p>
            } @else {
              <p class="text-xs" style="color: var(--text-muted)">No bills yet.</p>
            }
          </section>

          <!-- 3. Who owes whom -->
          @if (balances(); as b) {
            <section class="panel space-y-2">
              <h2 class="text-sm font-semibold">Who owes whom</h2>
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

  money(paise: number): string {
    return formatInr(paise);
  }
}
