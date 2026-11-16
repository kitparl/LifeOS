import { Component, Input, OnChanges, inject, signal } from '@angular/core';
import { formatMetric } from '../health.utils';
import { HealthDay } from '../models/health.models';
import { HealthService } from '../services/health.service';

const ITEMS = [
  { key: 'sleep_total_min', label: 'Sleep', unit: 'min' },
  { key: 'hrv_ms', label: 'HRV', unit: 'ms' },
  { key: 'body_battery_high', label: 'Body Battery', unit: '' },
];

/** How rested you were on the day of a run: sleep, HRV and Body Battery, when there is data for that date. */
@Component({
  selector: 'app-run-readiness',
  standalone: true,
  host: { class: 'contents' },
  template: `
    @if (items().length) {
      <div class="panel text-sm" data-testid="run-readiness">
        <p class="text-xs mb-1" style="color: var(--text-muted)">Recovery that day</p>
        <div class="flex flex-wrap gap-x-6 gap-y-1">
          @for (i of items(); track i.label) {
            <span><span style="color: var(--text-muted)">{{ i.label }}</span> <span class="font-medium">{{ i.value }}</span></span>
          }
        </div>
      </div>
    }
  `,
})
export class RunReadinessComponent implements OnChanges {
  private readonly health = inject(HealthService);

  /** The run date, YYYY-MM-DD (a longer ISO string is shortened). */
  @Input({ required: true }) date = '';

  readonly items = signal<{ label: string; value: string }[]>([]);

  ngOnChanges(): void {
    this.items.set([]);
    if (!this.date) return;
    this.health.getDay(this.date.slice(0, 10)).subscribe({
      next: (day: HealthDay) =>
        this.items.set(
          ITEMS.filter((i) => day.values[i.key] !== undefined).map((i) => ({
            label: i.label,
            value: formatMetric({ key: i.key, unit: i.unit }, day.values[i.key]),
          })),
        ),
      error: () => undefined, // no data for that day: show nothing
    });
  }
}
