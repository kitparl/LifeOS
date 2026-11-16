import { Component, Input, OnChanges, inject, signal } from '@angular/core';
import { clockLabel, paceLabel } from '../activity.utils';
import { ActivityDetail, ActivitySeries } from '../models/activity.models';
import { ActivityService } from '../services/activity.service';
import { RunChartsComponent } from './run-charts.component';
import { RunRouteMapComponent } from './run-route-map.component';
import { RunSplitsTableComponent } from './run-splits-table.component';

interface StatItem {
  label: string;
  value: string;
}

/** Everything recorded about an activity: summary numbers, route, charts, splits and laps. */
@Component({
  selector: 'app-activity-sections',
  standalone: true,
  imports: [RunChartsComponent, RunRouteMapComponent, RunSplitsTableComponent],
  host: { class: 'contents' },
  template: `
    @if (loading()) {
      <div class="panel"><div class="skeleton" style="width: 200px; height: 14px"></div></div>
    } @else if (failed()) {
      <p class="text-xs" style="color: var(--text-muted)" data-testid="activity-sections-error">
        The recorded details of this activity could not be loaded.
      </p>
    } @else {
      @if (detail(); as d) {
        @if (stats().length) {
          <div class="grid gap-3 sm:grid-cols-2 md:grid-cols-4" data-testid="activity-summary">
            @for (s of stats(); track s.label) {
              <div class="panel text-sm">
                <p class="text-xs" style="color: var(--text-muted)">{{ s.label }}</p>
                <p class="font-semibold mt-0.5">{{ s.value }}</p>
              </div>
            }
          </div>
        }
        @if (series(); as sr) {
          <app-run-route-map [route]="sr.route" />
          <app-run-charts [series]="sr" />
        }
        <app-run-splits-table [splits]="d.splits" [laps]="d.laps" />
      }
    }
  `,
})
export class ActivitySectionsComponent implements OnChanges {
  private readonly activities = inject(ActivityService);

  @Input({ required: true }) activityId = '';

  readonly detail = signal<ActivityDetail | null>(null);
  readonly series = signal<ActivitySeries | null>(null);
  readonly stats = signal<StatItem[]>([]);
  readonly loading = signal(false);
  readonly failed = signal(false);

  ngOnChanges(): void {
    if (!this.activityId) return;
    this.loading.set(true);
    this.failed.set(false);
    this.series.set(null);
    this.activities.getActivity(this.activityId).subscribe({
      next: (d) => {
        this.detail.set(d);
        this.stats.set(buildStats(d));
        this.loading.set(false);
        if (d.has_series) {
          this.activities.getActivitySeries(d.id).subscribe({ next: (s) => this.series.set(s) });
        }
      },
      error: () => {
        this.detail.set(null);
        this.failed.set(true);
        this.loading.set(false);
      },
    });
  }
}

/** Summary numbers; values the watch did not record are left out, never shown as zero. */
export function buildStats(d: ActivityDetail): StatItem[] {
  const running = d.sport.endsWith('running');
  const km = d.distance_m / 1000;
  const items: (StatItem | null)[] = [
    { label: 'Distance', value: `${km.toFixed(2)} km` },
    { label: 'Moving time', value: clockLabel(d.timer_seconds) },
    d.elapsed_seconds - d.timer_seconds > 5 ? { label: 'Elapsed time', value: clockLabel(d.elapsed_seconds) } : null,
    km > 0 ? { label: 'Average pace', value: paceLabel(d.timer_seconds / km) } : null,
    d.elevation_gain_m != null ? { label: 'Elevation gain', value: `${Math.round(d.elevation_gain_m)} m` } : null,
    d.avg_hr != null
      ? { label: 'Heart rate', value: d.max_hr != null ? `${d.avg_hr} avg · ${d.max_hr} max bpm` : `${d.avg_hr} bpm` }
      : null,
    d.avg_cadence != null
      ? { label: 'Cadence', value: `${Math.round(d.avg_cadence)} ${running ? 'spm' : 'rpm'}` }
      : null,
    d.calories != null ? { label: 'Calories', value: `${d.calories} kcal` } : null,
    d.training_effect_aerobic != null
      ? {
          label: 'Training effect',
          value:
            d.training_effect_anaerobic != null
              ? `${d.training_effect_aerobic.toFixed(1)} aerobic · ${d.training_effect_anaerobic.toFixed(1)} anaerobic`
              : `${d.training_effect_aerobic.toFixed(1)} aerobic`,
        }
      : null,
    d.device ? { label: 'Device', value: d.device } : null,
  ];
  return items.filter((i): i is StatItem => i !== null);
}
