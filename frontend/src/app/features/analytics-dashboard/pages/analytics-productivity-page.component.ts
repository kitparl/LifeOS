import { Component, OnInit, inject, signal } from '@angular/core';
import { AnalyticsDashboardService } from '../services/analytics-dashboard.service';
import { ProductivityAnalytics } from '../models/analytics-dashboard.models';
import { WidgetFrameComponent } from '../widgets/widget-frame.component';
import { KpiCardComponent } from '../widgets/kpi-card.component';
import { BarChartComponent } from '../../../shared/charts/bar-chart.component';
import { DonutChartComponent } from '../../../shared/charts/donut-chart.component';
import { HeatmapComponent } from '../../../shared/charts/heatmap.component';
import { LineChartComponent } from '../../../shared/charts/line-chart.component';

@Component({
  selector: 'app-analytics-productivity-page',
  standalone: true,
  imports: [
    WidgetFrameComponent,
    KpiCardComponent,
    BarChartComponent,
    DonutChartComponent,
    HeatmapComponent,
    LineChartComponent,
  ],
  template: `
    @if (loading()) {
      <p class="text-sm text-[var(--text-muted)]">Loading productivity…</p>
    } @else if (error()) {
      <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
    } @else if (data()) {
      <div class="space-y-4">
        <div class="grid gap-3 sm:grid-cols-3">
          <app-kpi-card title="Overdue Tasks" [value]="data()!.overdue_tasks" />
          <app-kpi-card
            title="Focus Hours"
            [value]="data()!.focus_hours"
            unit="h"
            [subtitle]="'Planned from routines'"
          />
          <app-kpi-card
            title="Deep Work"
            [value]="data()!.deep_work_hours"
            unit="h"
            [subtitle]="'DSA / Learning / Book'"
          />
        </div>

        <div class="grid gap-3 lg:grid-cols-2">
          <app-widget-frame title="Daily Tasks">
            <app-line-chart [points]="data()!.daily_tasks.points" title="Daily Tasks" />
          </app-widget-frame>
          <app-widget-frame title="Weekly Tasks">
            <app-bar-chart [points]="data()!.weekly_tasks.points" title="Weekly Tasks" />
          </app-widget-frame>
          <app-widget-frame title="Monthly Tasks">
            <app-bar-chart [points]="data()!.monthly_tasks.points" title="Monthly Tasks" />
          </app-widget-frame>
          <app-widget-frame title="Task Completion">
            <app-donut-chart [points]="data()!.task_completion" title="Task Completion" />
          </app-widget-frame>
          <app-widget-frame title="Category Distribution">
            <app-donut-chart [points]="data()!.category_distribution" title="Categories" />
          </app-widget-frame>
          <app-widget-frame title="Calendar Heatmap" hint="Completions">
            <app-heatmap [cells]="data()!.calendar_heatmap" title="Task heatmap" />
          </app-widget-frame>
        </div>
      </div>
    }
  `,
})
export class AnalyticsProductivityPageComponent implements OnInit {
  private readonly api = inject(AnalyticsDashboardService);
  readonly data = signal<ProductivityAnalytics | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.api.productivity().subscribe({
      next: (d) => {
        this.data.set(d);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load productivity');
        this.loading.set(false);
      },
    });
  }
}
