import { Component, OnInit, inject } from '@angular/core';
import {
  AnalyticsChartPoint,
  AnalyticsCharts,
  AnalyticsModuleCount,
  AnalyticsSummary,
} from './models/analytics.models';
import { AnalyticsService } from './services/analytics.service';

@Component({
  selector: 'app-analytics-page',
  standalone: true,
  template: `
    <div class="space-y-4">
      @if (summary) {
        <!-- Finance is reported in the Finance module as activity and obligations.
             Income minus expenses is deliberately not surfaced as a metric. -->
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div class="panel text-sm"><p class="text-gray-600">Tasks done</p><p class="text-xl font-semibold">{{ summary.tasks_completed }}</p></div>
          <div class="panel text-sm"><p class="text-gray-600">Habits (30d)</p><p class="text-xl font-semibold">{{ summary.habits_logged_30d }}</p></div>
          <div class="panel text-sm"><p class="text-gray-600">Runs (30d)</p><p class="text-xl font-semibold">{{ summary.runs_30d }}</p></div>
          <div class="panel text-sm"><p class="text-gray-600">Journal (30d)</p><p class="text-xl font-semibold">{{ summary.journal_entries_30d }}</p></div>
        </div>
        <div class="panel text-sm">
          <p class="mb-2 font-medium">Module counts</p>
          <ul class="grid gap-1 sm:grid-cols-2">
            @for (m of moduleCounts; track m.module) {
              <li>{{ m.module }}: {{ m.count }}</li>
            }
          </ul>
        </div>
      }
      @if (charts) {
        <div class="grid gap-3 lg:grid-cols-3">
          @for (section of chartSections; track section.title) {
            <div class="panel text-sm">
              <p class="mb-2 font-medium">{{ section.title }}</p>
              <ul class="space-y-1">
                @for (p of section.points; track p.label) {
                  <li class="flex justify-between gap-2"><span>{{ p.label }}</span><span>{{ p.value }}</span></li>
                }
              </ul>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class AnalyticsPageComponent implements OnInit {
  private readonly analytics = inject(AnalyticsService);
  summary: AnalyticsSummary | null = null;
  charts: AnalyticsCharts | null = null;
  moduleCounts: AnalyticsModuleCount[] = [];
  chartSections: { title: string; points: AnalyticsChartPoint[] }[] = [];

  ngOnInit(): void {
    this.analytics.summary().subscribe({
      next: (s) => {
        this.summary = s;
        this.moduleCounts = s.modules ?? [];
      },
    });
    this.analytics.charts().subscribe({
      next: (c) => {
        this.charts = c;
        this.chartSections = [
          { title: 'Tasks by status', points: c.tasks_by_status ?? [] },
          { title: 'Expenses by category', points: c.expenses_by_category ?? [] },
          { title: 'Learning by type', points: c.learning_by_type ?? [] },
        ];
      },
    });
  }
}
