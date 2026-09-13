import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { TabHubComponent } from '../../shared/tab-hub/tab-hub.component';
import { AnalyticsPageComponent } from '../analytics/analytics-page.component';
import { PredictionsPageComponent } from '../predictions/predictions-page.component';
import { ReportsPageComponent } from '../reports/reports-page.component';

type InsightsTab = 'overview' | 'reports' | 'predictions';

@Component({
  selector: 'app-insights-hub',
  standalone: true,
  imports: [TabHubComponent, AnalyticsPageComponent, ReportsPageComponent, PredictionsPageComponent],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Insights</h1>

      <app-tab-hub [tabs]="tabs" [activeId]="tab()" (tabChange)="setTab($event)" />

      @if (tab() === 'overview') {
        <app-analytics-page />
      } @else if (tab() === 'reports') {
        <app-reports-page />
      } @else {
        <app-predictions-page />
      }
    </div>
  `,
})
export class InsightsHubComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly tab = signal<InsightsTab>('overview');
  readonly tabs = [
    { id: 'overview' as const, label: 'Overview' },
    { id: 'reports' as const, label: 'Reports' },
    { id: 'predictions' as const, label: 'Predictions' },
  ];

  ngOnInit(): void {
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const t = params.get('tab');
      if (t === 'reports' || t === 'predictions') {
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
