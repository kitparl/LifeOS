import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { TabHubComponent } from '../../shared/tab-hub/tab-hub.component';
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
    TabHubComponent,
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

      <app-tab-hub [tabs]="tabs" [activeId]="tab()" [wrap]="true" (tabChange)="setTab($event)" />

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
  private readonly destroyRef = inject(DestroyRef);

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
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const t = params.get('tab') as AnalyticsTab | null;
      if (t && this.valid.has(t)) {
        this.tab.set(t);
      } else {
        this.tab.set('overview');
      }
    });
  }

  setTab(id: string): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id === 'overview' ? null : id },
      queryParamsHandling: 'merge',
    });
  }
}
