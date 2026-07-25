import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AnalyticsTab } from './models/analytics-dashboard.models';
import { AnalyticsOverviewPageComponent } from './pages/analytics-overview-page.component';
import { AnalyticsProductivityPageComponent } from './pages/analytics-productivity-page.component';
import { AnalyticsGoalsPageComponent } from './pages/analytics-goals-page.component';
import { AnalyticsHabitsPageComponent } from './pages/analytics-habits-page.component';
import { AnalyticsJournalPageComponent } from './pages/analytics-journal-page.component';
import { AnalyticsAiPageComponent } from './pages/analytics-ai-page.component';

@Component({
  selector: 'app-analytics-dashboard-hub',
  standalone: true,
  imports: [
    AnalyticsOverviewPageComponent,
    AnalyticsProductivityPageComponent,
    AnalyticsGoalsPageComponent,
    AnalyticsHabitsPageComponent,
    AnalyticsJournalPageComponent,
    AnalyticsAiPageComponent,
  ],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Analytics</h1>

      <div class="flex flex-wrap gap-1 border-b border-[var(--xp-border)] text-sm">
        @for (t of tabs; track t.id) {
          <button
            type="button"
            class="px-3 py-2"
            [class.bg-[var(--xp-blue)]]="tab() === t.id"
            [class.text-white]="tab() === t.id"
            (click)="setTab(t.id)"
          >
            {{ t.label }}
          </button>
        }
      </div>

      @if (tab() === 'overview') {
        <app-analytics-overview-page />
      } @else if (tab() === 'productivity') {
        <app-analytics-productivity-page />
      } @else if (tab() === 'goals') {
        <app-analytics-goals-page />
      } @else if (tab() === 'habits') {
        <app-analytics-habits-page />
      } @else if (tab() === 'journal') {
        <app-analytics-journal-page />
      } @else {
        <app-analytics-ai-page />
      }
    </div>
  `,
})
export class AnalyticsDashboardHubComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly tab = signal<AnalyticsTab>('overview');
  readonly tabs = [
    { id: 'overview' as const, label: 'Dashboard' },
    { id: 'productivity' as const, label: 'Productivity' },
    { id: 'goals' as const, label: 'Goals' },
    { id: 'habits' as const, label: 'Habits' },
    { id: 'journal' as const, label: 'Journal' },
    { id: 'ai' as const, label: 'AI Insights' },
  ];

  private readonly valid = new Set<AnalyticsTab>([
    'overview',
    'productivity',
    'goals',
    'habits',
    'journal',
    'ai',
  ]);

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      const t = params.get('tab') as AnalyticsTab | null;
      if (t && this.valid.has(t)) {
        this.tab.set(t);
      } else {
        this.tab.set('overview');
      }
    });
  }

  setTab(id: AnalyticsTab): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id === 'overview' ? null : id },
      queryParamsHandling: 'merge',
    });
  }
}
