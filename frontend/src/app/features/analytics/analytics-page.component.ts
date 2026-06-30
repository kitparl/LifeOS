import { Component, OnInit, inject } from '@angular/core';
import { AnalyticsService } from './services/analytics.service';

@Component({
  selector: 'app-analytics-page',
  standalone: true,
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">Analytics</h1>
      @if (summary) {
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div class="panel text-sm"><p class="text-gray-600">Tasks done</p><p class="text-xl font-semibold">{{ summary['tasks_completed'] }}</p></div>
          <div class="panel text-sm"><p class="text-gray-600">Habits (30d)</p><p class="text-xl font-semibold">{{ summary['habits_logged_30d'] }}</p></div>
          <div class="panel text-sm"><p class="text-gray-600">Runs (30d)</p><p class="text-xl font-semibold">{{ summary['runs_30d'] }}</p></div>
          <div class="panel text-sm"><p class="text-gray-600">Finance net</p><p class="text-xl font-semibold">{{ summary['finance_net'] }}</p></div>
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
  summary: Record<string, unknown> | null = null;
  charts: Record<string, unknown> | null = null;
  moduleCounts: { module: string; count: number }[] = [];
  chartSections: { title: string; points: { label: string; value: number }[] }[] = [];

  ngOnInit(): void {
    this.analytics.summary().subscribe({
      next: (s) => {
        this.summary = s;
        this.moduleCounts = (s['modules'] as { module: string; count: number }[]) ?? [];
      },
    });
    this.analytics.charts().subscribe({
      next: (c) => {
        this.charts = c;
        this.chartSections = [
          { title: 'Tasks by status', points: (c['tasks_by_status'] as { label: string; value: number }[]) ?? [] },
          { title: 'Expenses by category', points: (c['expenses_by_category'] as { label: string; value: number }[]) ?? [] },
          { title: 'Learning by type', points: (c['learning_by_type'] as { label: string; value: number }[]) ?? [] },
        ];
      },
    });
  }
}
