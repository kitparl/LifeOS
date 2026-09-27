import { DatePipe } from '@angular/common';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { apiErrorMessage } from '../../../core/utils/http';
import { SplitShareActionsComponent } from '../components/share-actions.component';
import { SplitGroupView, SplitMember } from '../models/split.models';
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
  imports: [DatePipe, RouterLink, SplitShareActionsComponent],
  template: `
    <div class="min-h-dvh" style="background: var(--page-bg); color: var(--text)">
      <header
        class="flex items-center justify-between gap-2 px-4 py-2"
        style="background: var(--sidebar-bg); border-bottom: 1px solid var(--border)"
      >
        <a class="text-sm font-semibold" [routerLink]="homeLink()">LifeOS · Split bills</a>
        @if (!auth.isAuthenticated()) {
          <a class="btn-ghost text-xs" routerLink="/login">Sign in</a>
        }
      </header>

      <main class="mx-auto max-w-3xl space-y-4 p-4">
        @if (error()) {
          <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
        }

        @if (group(); as g) {
          <section class="panel space-y-3" data-testid="split-group-header">
            <div class="flex flex-wrap items-baseline justify-between gap-2">
              <h1 class="text-base font-semibold">{{ g.name }}</h1>
              <span class="chip text-xs" data-testid="split-link-status">{{ status() }}</span>
            </div>
            <app-split-share-actions [groupName]="g.name" [urlPath]="g.url_path" />
          </section>

          <section class="panel space-y-2">
            <h2 class="text-sm font-semibold">People ({{ g.members.length }})</h2>
            <ul class="flex flex-wrap gap-2 text-xs" data-testid="split-members">
              @for (m of g.members; track m.id) {
                <li class="chip">
                  {{ m.display_name }}{{ m.id === g.my_member_id ? ' (you)' : '' }}{{ m.is_creator ? ' · creator' : '' }}
                </li>
              }
            </ul>
            @if (g.members.length === 1) {
              <p class="text-xs" style="color: var(--text-muted)">Share the link. People join only if they want to.</p>
            }
          </section>

          <section class="panel !p-0 overflow-hidden">
            <h2 class="px-3 pt-3 text-sm font-semibold">Bills</h2>
            @if (g.expenses.length) {
              <ul class="divide-y divide-[var(--xp-border)] text-sm" data-testid="split-bills">
                @for (e of g.expenses; track e.id) {
                  <li class="px-3 py-2" data-testid="split-bill-row">
                    <div class="flex items-center justify-between gap-2">
                      <p class="min-w-0 truncate">{{ e.title }}</p>
                      <span class="font-medium">{{ money(e.amount_paise) }}</span>
                    </div>
                    <p class="text-xs" style="color: var(--text-muted)">
                      Paid by {{ memberName(e.paid_by) }} · {{ e.expense_date | date: 'dd MMM' }} ·
                      @for (s of e.shares; track s.member_id; let last = $last) {
                        {{ memberName(s.member_id) }} {{ money(s.amount_paise) }}{{ last ? '' : ', ' }}
                      }
                    </p>
                  </li>
                }
              </ul>
            } @else {
              <p class="p-3 text-sm" style="color: var(--text-muted)">No bills yet.</p>
            }
          </section>
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
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  private readonly now = signal(Date.now());

  readonly code = this.route.snapshot.paramMap.get('code') ?? '';

  readonly status = computed(() => {
    const g = this.group();
    return g ? linkStatusLabel(g, this.now()) : '';
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
    this.api.getGroup(this.code, this.store.find(this.code)?.seatSecret).subscribe({
      next: (group) => {
        this.group.set(group);
        this.error.set(null);
        this.loading.set(false);
      },
      error: (err: unknown) => {
        this.error.set(apiErrorMessage(err, 'Could not load this group.'));
        this.loading.set(false);
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
