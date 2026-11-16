import { Component, Input, OnChanges, OnInit, inject, signal } from '@angular/core';
import { formatMetric } from '../health.utils';
import { HEALTH_RANGES, HealthRange, METRIC_GROUPS, MetricInfo, MetricSeries } from '../models/health.models';
import { HealthService } from '../services/health.service';
import { HealthTrendChartComponent } from './health-trend-chart.component';

/** One metric over 7 days to 1 year. */
@Component({
  selector: 'app-health-trends-tab',
  standalone: true,
  imports: [HealthTrendChartComponent],
  host: { class: 'contents' },
  template: `
    <div class="flex flex-wrap items-center gap-2 text-sm">
      <label class="text-xs" style="color: var(--text-muted)" for="health-trend-metric">Metric</label>
      <select
        id="health-trend-metric"
        class="input-field !w-auto"
        data-testid="health-trend-metric-select"
        [value]="key()"
        (change)="onMetric($event)"
      >
        @for (g of groups; track g.id) {
          <optgroup [label]="g.label">
            @for (m of metricsOf(g.id); track m.key) {
              <option [value]="m.key">{{ m.label }}</option>
            }
          </optgroup>
        }
      </select>
      <div class="flex gap-1" role="group" aria-label="Range">
        @for (r of ranges; track r.value) {
          <button
            type="button"
            class="btn-secondary text-xs"
            [class.btn-primary]="range() === r.value"
            [attr.data-testid]="'health-trend-range-' + r.value"
            [attr.aria-pressed]="range() === r.value"
            (click)="setRange(r.value)"
          >{{ r.label }}</button>
        }
      </div>
    </div>

    <div class="panel space-y-2">
      @if (loading()) {
        <div class="skeleton" style="width: 200px; height: 14px"></div>
      } @else if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
      } @else {
        @if (series(); as s) {
          <p class="text-xs" style="color: var(--text-muted)" data-testid="health-trend-caption">
            Average {{ show(s.average) }} · lowest {{ show(s.minimum) }} · highest {{ show(s.maximum) }}
          </p>
          <app-health-trend-chart
            [points]="s.points"
            [rollingPoints]="s.rolling"
            [label]="s.label"
            [unit]="s.unit"
            [kind]="kind()"
          />
        }
      }
    </div>
  `,
})
export class HealthTrendsTabComponent implements OnInit, OnChanges {
  private readonly health = inject(HealthService);

  @Input({ required: true }) catalogue: MetricInfo[] = [];
  @Input() refresh = 0;

  readonly ranges = HEALTH_RANGES;
  readonly groups = METRIC_GROUPS;
  readonly key = signal('resting_hr');
  readonly range = signal<HealthRange>('30d');
  readonly series = signal<MetricSeries | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');

  ngOnInit(): void {
    this.load();
  }

  ngOnChanges(changes: { refresh?: unknown }): void {
    if (changes.refresh && this.series()) this.load();
  }

  metricsOf(group: string): MetricInfo[] {
    return this.catalogue.filter((m) => m.group === group);
  }

  kind(): MetricInfo['kind'] {
    return this.catalogue.find((m) => m.key === this.key())?.kind ?? 'float';
  }

  show(value: number | null): string {
    const s = this.series();
    return s ? formatMetric({ key: s.key, unit: s.unit, kind: this.kind() }, value) : '—';
  }

  onMetric(event: Event): void {
    this.key.set((event.target as HTMLSelectElement).value);
    this.load();
  }

  setRange(range: HealthRange): void {
    this.range.set(range);
    this.load();
  }

  private load(): void {
    this.loading.set(true);
    this.error.set('');
    this.health.getMetricSeries(this.key(), this.range()).subscribe({
      next: (s) => {
        this.series.set(s);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('The trend could not be loaded.');
        this.loading.set(false);
      },
    });
  }
}
