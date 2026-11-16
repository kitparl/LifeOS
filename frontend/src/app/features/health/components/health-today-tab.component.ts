import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, Output, inject, signal } from '@angular/core';
import { formatMetric, markerLabel, markerSymbol } from '../health.utils';
import { HealthToday, TodayMetric } from '../models/health.models';
import { HealthService } from '../services/health.service';

/** The latest day against your own 7-day and 30-day averages. */
@Component({
  selector: 'app-health-today-tab',
  standalone: true,
  imports: [DatePipe],
  host: { class: 'contents' },
  template: `
    @if (loading()) {
      <div class="panel"><div class="skeleton" style="width: 200px; height: 14px"></div></div>
    } @else if (error()) {
      <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
    } @else {
      @if (today(); as t) {
        @if (!t.day) {
          <div class="panel empty-state" data-testid="health-today-empty">
            <p class="empty-state__title">No health data yet</p>
            <p class="empty-state__desc">Log a day to start seeing how you compare with your own averages.</p>
            <button type="button" class="btn-primary text-xs mt-2" data-testid="health-today-log-button" (click)="logDay.emit()">
              Log a day
            </button>
          </div>
        } @else {
          <p class="text-sm" style="color: var(--text-muted)" data-testid="health-today-date">
            @if (t.is_today) {
              Today, {{ t.day | date: 'mediumDate' }}
            } @else {
              Latest data: {{ t.day | date: 'mediumDate' }}
            }
          </p>
          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            @for (m of t.metrics; track m.key) {
              <div class="panel" [attr.data-testid]="'health-today-card-' + m.key">
                <p class="text-xs" style="color: var(--text-muted)">{{ m.label }}</p>
                <p class="text-xl font-semibold mt-0.5">{{ show(m, m.value) }}</p>
                @if (m.marker) {
                  <p class="text-xs mt-1" [style.color]="color(m)">
                    {{ symbol(m) }} {{ label(m) }}@if (m.favourable === 'good') { (better) }@if (m.favourable === 'bad') { (worse) }
                  </p>
                } @else if (m.needs_more_data) {
                  <p class="text-xs mt-1" style="color: var(--text-muted)">More data needed for a comparison</p>
                }
                @if (m.avg_7d !== null || m.avg_30d !== null) {
                  <p class="text-xs mt-1" style="color: var(--text-muted)">
                    7-day average {{ show(m, m.avg_7d) }} · 30-day average {{ show(m, m.avg_30d) }}
                  </p>
                }
              </div>
            }
          </div>
        }
      }
    }
  `,
})
export class HealthTodayTabComponent implements OnChanges {
  private readonly health = inject(HealthService);

  /** Changing this reloads the tab (the page bumps it after a day is saved). */
  @Input() refresh = 0;
  @Output() readonly logDay = new EventEmitter<void>();

  readonly today = signal<HealthToday | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');

  readonly symbol = (m: TodayMetric) => markerSymbol(m.marker);
  readonly label = (m: TodayMetric) => markerLabel(m.marker);

  ngOnChanges(): void {
    this.loading.set(this.today() === null);
    this.error.set('');
    this.health.getToday().subscribe({
      next: (t) => {
        this.today.set(t);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Health data could not be loaded.');
        this.loading.set(false);
      },
    });
  }

  show(m: TodayMetric, value: number | null): string {
    return formatMetric({ key: m.key, unit: m.unit }, value);
  }

  color(m: TodayMetric): string {
    return m.favourable === 'good' ? 'var(--success)' : m.favourable === 'bad' ? 'var(--danger)' : 'var(--text-muted)';
  }
}
