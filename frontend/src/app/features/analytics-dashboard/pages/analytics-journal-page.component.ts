import { Component, OnInit, inject, signal } from '@angular/core';
import { AnalyticsDashboardService } from '../services/analytics-dashboard.service';
import { JournalAnalytics } from '../models/analytics-dashboard.models';
import { WidgetFrameComponent } from '../widgets/widget-frame.component';
import { KpiCardComponent } from '../widgets/kpi-card.component';
import { LineChartComponent } from '../../../shared/charts/line-chart.component';
import { BarChartComponent } from '../../../shared/charts/bar-chart.component';

@Component({
  selector: 'app-analytics-journal-page',
  standalone: true,
  imports: [WidgetFrameComponent, KpiCardComponent, LineChartComponent, BarChartComponent],
  template: `
    @if (loading()) {
      <p class="text-sm text-[var(--text-muted)]">Loading journal…</p>
    } @else if (error()) {
      <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
    } @else if (data()) {
      <div class="space-y-4">
        <div class="grid gap-3 sm:grid-cols-3">
          <app-kpi-card title="Writing Streak" [value]="data()!.writing_streak" unit="days" />
          <app-kpi-card title="Word Count" [value]="data()!.word_count_total" />
          <app-kpi-card
            title="Sentiment"
            [value]="data()!.sentiment.message || 'Coming Soon'"
          />
        </div>

        <div class="grid gap-3 lg:grid-cols-2">
          <app-widget-frame title="Journal Frequency">
            <app-bar-chart [points]="data()!.journal_frequency.points" title="Frequency" />
          </app-widget-frame>
          <app-widget-frame title="Word Count">
            <app-line-chart [points]="data()!.word_count_series.points" title="Words" />
          </app-widget-frame>
        </div>

        @if (data()!.mood_trend.length) {
          <div class="grid gap-3 lg:grid-cols-2">
            @for (series of data()!.mood_trend; track series.key) {
              <app-widget-frame [title]="'Mood: ' + series.label">
                <app-line-chart [points]="series.points" [title]="series.label" />
              </app-widget-frame>
            }
          </div>
        } @else {
          <app-widget-frame title="Mood Trend">
            <p class="text-sm text-[var(--text-muted)]">No mood entries in range</p>
          </app-widget-frame>
        }

        <app-widget-frame title="Emotion" hint="AI placeholder">
          <p class="text-sm text-[var(--text-muted)]">{{ data()!.emotion.message || 'Coming Soon' }}</p>
        </app-widget-frame>
      </div>
    }
  `,
})
export class AnalyticsJournalPageComponent implements OnInit {
  private readonly api = inject(AnalyticsDashboardService);
  readonly data = signal<JournalAnalytics | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.api.journal().subscribe({
      next: (d) => {
        this.data.set(d);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load journal');
        this.loading.set(false);
      },
    });
  }
}
