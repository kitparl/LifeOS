import { DatePipe } from '@angular/common';
import { Component, Input, OnChanges, OnInit, inject, signal } from '@angular/core';
import { minutesToClock, sleepLabel } from '../health.utils';
import { HealthDay, HealthRange, SleepResponse } from '../models/health.models';
import { HealthService } from '../services/health.service';

const SLEEP_RANGES: { value: HealthRange; label: string }[] = [
  { value: '7d', label: '7 days' },
  { value: '30d', label: '30 days' },
  { value: '90d', label: '90 days' },
];

const STAGES = [
  { key: 'sleep_deep_min', label: 'Deep', color: 'var(--primary)' },
  { key: 'sleep_light_min', label: 'Light', color: 'var(--text-faint)' },
  { key: 'sleep_rem_min', label: 'REM', color: 'var(--success)' },
  { key: 'sleep_awake_min', label: 'Awake', color: 'var(--danger)' },
];

/** Nightly sleep stages, bed and wake times and how consistent they are. */
@Component({
  selector: 'app-health-sleep-tab',
  standalone: true,
  imports: [DatePipe],
  host: { class: 'contents' },
  template: `
    <div class="flex gap-1" role="group" aria-label="Range">
      @for (r of ranges; track r.value) {
        <button
          type="button"
          class="btn-secondary text-xs"
          [class.btn-primary]="range() === r.value"
          [attr.data-testid]="'health-sleep-range-' + r.value"
          [attr.aria-pressed]="range() === r.value"
          (click)="setRange(r.value)"
        >{{ r.label }}</button>
      }
    </div>

    @if (loading()) {
      <div class="panel"><div class="skeleton" style="width: 200px; height: 14px"></div></div>
    } @else if (error()) {
      <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
    } @else {
      @if (sleep(); as s) {
        <div class="panel text-sm" data-testid="health-sleep-consistency">
          @if (s.consistency.bed_time_sd_min !== null && s.consistency.wake_time_sd_min !== null) {
            Bed time varies by about {{ round(s.consistency.bed_time_sd_min) }} min and wake time by about
            {{ round(s.consistency.wake_time_sd_min) }} min across {{ s.consistency.nights }} nights.
          } @else {
            More nights with bed and wake times are needed to show how consistent your sleep is.
          }
        </div>
        <div class="panel !p-0 overflow-hidden">
          @if (!s.nights.length) {
            <div class="empty-state">
              <p class="empty-state__title">No sleep recorded in this range</p>
              <p class="empty-state__desc">Use "Log a day" to add sleep.</p>
            </div>
          } @else {
            <div class="overflow-x-auto">
              <table class="w-full text-sm" style="min-width: 560px" data-testid="health-sleep-table">
                <thead>
                  <tr>
                    <th class="px-3 py-2 text-left">Night</th>
                    <th class="px-3 py-2 text-left">Total</th>
                    <th class="px-3 py-2 text-left">Stages</th>
                    <th class="px-3 py-2 text-left">Bed</th>
                    <th class="px-3 py-2 text-left">Wake</th>
                    <th class="px-3 py-2 text-left">Score</th>
                  </tr>
                </thead>
                <tbody>
                  @for (n of s.nights; track n.day) {
                    <tr style="border-bottom: 1px solid var(--border)">
                      <td class="px-3 py-2">{{ n.day | date: 'mediumDate' }}</td>
                      <td class="px-3 py-2">{{ sleepText(n.values['sleep_total_min']) }}</td>
                      <td class="px-3 py-2" style="min-width: 10rem">
                        @if (stageShares(n); as shares) {
                          <div class="flex h-2 w-full overflow-hidden rounded" role="img" [attr.aria-label]="stageSummary(n)">
                            @for (sh of shares; track sh.key) {
                              <div [style.width.%]="sh.percent" [style.background]="sh.color"></div>
                            }
                          </div>
                          <p class="text-xs mt-0.5" style="color: var(--text-muted)">{{ stageSummary(n) }}</p>
                        } @else {
                          <span style="color: var(--text-muted)">—</span>
                        }
                      </td>
                      <td class="px-3 py-2">{{ clock(n.values['bed_time_min']) }}</td>
                      <td class="px-3 py-2">{{ clock(n.values['wake_time_min']) }}</td>
                      <td class="px-3 py-2">{{ n.values['sleep_score'] ?? '—' }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          }
        </div>
      }
    }
  `,
})
export class HealthSleepTabComponent implements OnInit, OnChanges {
  private readonly health = inject(HealthService);

  @Input() refresh = 0;

  readonly ranges = SLEEP_RANGES;
  readonly range = signal<HealthRange>('30d');
  readonly sleep = signal<SleepResponse | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');

  ngOnInit(): void {
    this.load();
  }

  ngOnChanges(changes: { refresh?: unknown }): void {
    if (changes.refresh && this.sleep()) this.load();
  }

  setRange(range: HealthRange): void {
    this.range.set(range);
    this.load();
  }

  round(value: number): number {
    return Math.round(value);
  }

  sleepText(minutes: number | undefined): string {
    return sleepLabel(minutes);
  }

  clock(minutes: number | undefined): string {
    return minutes === undefined ? '—' : minutesToClock(minutes);
  }

  /** Shares of the recorded stages; null for a night with only a total. */
  stageShares(night: HealthDay): { key: string; percent: number; color: string }[] | null {
    const parts = STAGES.map((s) => ({ ...s, minutes: night.values[s.key] ?? 0 }));
    const total = parts.reduce((sum, p) => sum + p.minutes, 0);
    if (total <= 0) return null;
    return parts.filter((p) => p.minutes > 0).map((p) => ({ key: p.key, percent: (p.minutes / total) * 100, color: p.color }));
  }

  stageSummary(night: HealthDay): string {
    return STAGES.filter((s) => night.values[s.key] !== undefined)
      .map((s) => `${s.label} ${sleepLabel(night.values[s.key])}`)
      .join(' · ');
  }

  private load(): void {
    this.loading.set(this.sleep() === null);
    this.error.set('');
    this.health.getSleep(this.range()).subscribe({
      next: (s) => {
        this.sleep.set(s);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Sleep data could not be loaded.');
        this.loading.set(false);
      },
    });
  }
}
