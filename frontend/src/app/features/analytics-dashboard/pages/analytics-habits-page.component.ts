import { Component, OnInit, inject, signal } from '@angular/core';
import { AnalyticsDashboardService } from '../services/analytics-dashboard.service';
import { HabitAnalytics } from '../models/analytics-dashboard.models';
import { WidgetFrameComponent } from '../widgets/widget-frame.component';
import { KpiCardComponent } from '../widgets/kpi-card.component';
import { HeatmapComponent } from '../../../shared/charts/heatmap.component';

@Component({
  selector: 'app-analytics-habits-page',
  standalone: true,
  imports: [WidgetFrameComponent, KpiCardComponent, HeatmapComponent],
  template: `
    @if (loading()) {
      <p class="text-sm text-[var(--text-muted)]">Loading habits…</p>
    } @else if (error()) {
      <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
    } @else if (data()) {
      <div class="space-y-4">
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <app-kpi-card title="Current Streak" [value]="data()!.current_streak_max" unit="d" />
          <app-kpi-card title="Longest Streak" [value]="data()!.longest_streak_max" unit="d" />
          <app-kpi-card title="Consistency" [value]="data()!.consistency_avg" unit="%" />
          <app-kpi-card title="Weekly Completion" [value]="data()!.weekly_completion_avg" unit="%" />
        </div>

        <div class="grid gap-3 sm:grid-cols-2">
          <app-kpi-card title="Best Habit" [value]="data()!.best_habit || '—'" />
          <app-kpi-card title="Worst Habit" [value]="data()!.worst_habit || '—'" />
        </div>

        <app-widget-frame title="Habit Heatmap">
          <app-heatmap [cells]="data()!.heatmap" title="Habit heatmap" />
        </app-widget-frame>

        @if (data()!.habits.length) {
          <app-widget-frame title="Per Habit">
            <ul class="divide-y divide-[var(--xp-border)] text-sm">
              @for (h of data()!.habits; track h.id) {
                <li class="flex flex-wrap justify-between gap-2 py-2">
                  <span class="font-medium">{{ h.name }}</span>
                  <span class="text-[var(--text-muted)]">
                    streak {{ h.current_streak }} · {{ h.consistency_pct }}% · W {{ h.weekly_completion }}% · M
                    {{ h.monthly_completion }}%
                  </span>
                </li>
              }
            </ul>
          </app-widget-frame>
        }
      </div>
    }
  `,
})
export class AnalyticsHabitsPageComponent implements OnInit {
  private readonly api = inject(AnalyticsDashboardService);
  readonly data = signal<HabitAnalytics | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.api.habits().subscribe({
      next: (d) => {
        this.data.set(d);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load habits');
        this.loading.set(false);
      },
    });
  }
}
