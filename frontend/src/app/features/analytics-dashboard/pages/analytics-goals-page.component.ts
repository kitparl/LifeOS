import { Component, OnInit, inject, signal } from '@angular/core';
import { AnalyticsDashboardService } from '../services/analytics-dashboard.service';
import { GoalAnalytics } from '../models/analytics-dashboard.models';
import { WidgetFrameComponent } from '../widgets/widget-frame.component';
import { KpiCardComponent } from '../widgets/kpi-card.component';
import { ProgressRingComponent } from '../../../shared/charts/progress-ring.component';
import { BurndownChartComponent } from '../../../shared/charts/burndown-chart.component';

@Component({
  selector: 'app-analytics-goals-page',
  standalone: true,
  imports: [WidgetFrameComponent, KpiCardComponent, ProgressRingComponent, BurndownChartComponent],
  template: `
    @if (loading()) {
      <p class="text-sm text-[var(--text-muted)]">Loading goals…</p>
    } @else if (error()) {
      <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
    } @else if (data()) {
      <div class="space-y-4">
        <div class="grid gap-3 sm:grid-cols-2">
          <app-kpi-card title="Avg Progress" [value]="data()!.avg_progress" unit="%" />
          <app-kpi-card title="Avg Velocity" [value]="data()!.avg_velocity" unit="/wk" />
        </div>

        @if (!data()!.goals.length) {
          <p class="text-sm text-[var(--text-muted)]">No goals yet</p>
        } @else {
          <div class="grid gap-3 lg:grid-cols-2">
            @for (g of data()!.goals; track g.id) {
              <app-widget-frame [title]="g.title" [hint]="g.status">
                <div class="flex flex-wrap items-start gap-4">
                  <app-progress-ring [value]="g.progress" title="Progress" />
                  <div class="space-y-1 text-sm flex-1 min-w-[10rem]">
                    <p>Remaining tasks: <strong>{{ g.remaining_tasks }}</strong></p>
                    <p>Milestones: <strong>{{ g.milestones_done }}/{{ g.milestones_total }}</strong></p>
                    <p>Velocity: <strong>{{ g.velocity }}</strong>/wk</p>
                    <p class="text-xs text-[var(--text-muted)]">
                      Forecast: {{ g.completion_forecast.message || 'Coming Soon' }}
                    </p>
                    <p class="text-xs text-[var(--text-muted)]">
                      Risk: {{ g.risk_indicator.message || 'Coming Soon' }}
                    </p>
                  </div>
                </div>
                <div class="mt-3">
                  <p class="mb-1 text-xs text-[var(--text-muted)]">Burndown</p>
                  <app-burndown-chart [points]="g.burndown" [title]="g.title + ' burndown'" />
                </div>
              </app-widget-frame>
            }
          </div>
        }
      </div>
    }
  `,
})
export class AnalyticsGoalsPageComponent implements OnInit {
  private readonly api = inject(AnalyticsDashboardService);
  readonly data = signal<GoalAnalytics | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.api.goals().subscribe({
      next: (d) => {
        this.data.set(d);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load goals');
        this.loading.set(false);
      },
    });
  }
}
