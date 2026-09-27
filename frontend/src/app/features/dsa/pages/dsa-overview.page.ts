import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DsaStateComponent } from '../components/dsa-state.component';
import { PatternSummary } from '../models/dsa.models';
import { DsaService } from '../services/dsa.service';

interface WeekGroup {
  week: number;
  patterns: PatternSummary[];
}

@Component({
  selector: 'app-dsa-overview-page',
  standalone: true,
  imports: [RouterLink, DsaStateComponent],
  template: `
    <div class="mx-auto max-w-6xl space-y-6">
      <header class="space-y-1">
        <h1 class="text-xl font-semibold">DSA Practice</h1>
        <p class="text-sm" style="color: var(--text-muted)">
          29 coding-interview patterns. Pick a pattern, solve its problems, and track your progress.
        </p>
        @if (totals(); as t) {
          <p class="text-xs" style="color: var(--text-muted)" data-testid="dsa-overview-totals">
            {{ t.solved }} solved · {{ t.attempted }} attempted · {{ t.total }} available
          </p>
        }
      </header>

      @if (loading()) {
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          @for (i of skeletons; track i) {
            <div class="panel skeleton h-28"></div>
          }
        </div>
      } @else if (error()) {
        <app-dsa-state title="We couldn't load the patterns." [retryable]="true" (retry)="load()" />
      } @else {
        @for (group of weeks(); track group.week) {
          <section class="space-y-2" [attr.aria-label]="'Week ' + group.week">
            <h2 class="section-heading">Week {{ group.week }}</h2>
            <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              @for (p of group.patterns; track p.slug) {
                <a
                  class="panel flex flex-col gap-2 no-underline transition-colors hover:border-[var(--primary)]"
                  style="color: inherit"
                  [routerLink]="['patterns', p.slug]"
                  [attr.data-testid]="'dsa-overview-pattern-' + p.slug"
                >
                  <div class="flex items-baseline justify-between gap-2">
                    <span class="font-medium">{{ p.number }}. {{ p.name }}</span>
                    <span class="shrink-0 text-xs" style="color: var(--text-muted)">{{ p.solved }}/{{ p.total }}</span>
                  </div>
                  <p class="line-clamp-2 text-xs" style="color: var(--text-muted)">{{ p.description }}</p>
                  <div class="progress-bar mt-auto" role="progressbar" [attr.aria-valuenow]="p.solved" [attr.aria-valuemax]="p.total">
                    <div class="progress-bar__fill" [style.width.%]="percent(p)"></div>
                  </div>
                  @if (p.total === 0) {
                    <span class="text-xs" style="color: var(--text-faint)">Problems coming soon</span>
                  } @else if (p.attempted > 0) {
                    <span class="text-xs" style="color: var(--text-muted)">{{ p.attempted }} in progress</span>
                  }
                </a>
              }
            </div>
          </section>
        }
      }
    </div>
  `,
})
export class DsaOverviewPageComponent implements OnInit {
  private readonly dsa = inject(DsaService);

  readonly skeletons = [1, 2, 3, 4, 5, 6];
  readonly patterns = signal<PatternSummary[]>([]);
  readonly loading = signal(true);
  readonly error = signal(false);

  readonly weeks = computed<WeekGroup[]>(() => {
    const byWeek = new Map<number, PatternSummary[]>();
    for (const p of this.patterns()) {
      byWeek.set(p.week, [...(byWeek.get(p.week) ?? []), p]);
    }
    return [...byWeek.entries()].sort(([a], [b]) => a - b).map(([week, patterns]) => ({ week, patterns }));
  });

  readonly totals = computed(() => {
    const list = this.patterns();
    if (list.length === 0) return null;
    return list.reduce(
      (acc, p) => ({ solved: acc.solved + p.solved, attempted: acc.attempted + p.attempted, total: acc.total + p.total }),
      { solved: 0, attempted: 0, total: 0 },
    );
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(false);
    this.dsa.patterns().subscribe({
      next: (list) => {
        this.patterns.set(list);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }

  percent(p: PatternSummary): number {
    return p.total === 0 ? 0 : Math.round((p.solved / p.total) * 100);
  }
}
