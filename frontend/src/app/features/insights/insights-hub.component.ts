import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AnalyticsPageComponent } from '../analytics/analytics-page.component';
import { PredictionsPageComponent } from '../predictions/predictions-page.component';
import { ReportsPageComponent } from '../reports/reports-page.component';

type InsightsTab = 'overview' | 'reports' | 'predictions';

@Component({
  selector: 'app-insights-hub',
  standalone: true,
  imports: [AnalyticsPageComponent, ReportsPageComponent, PredictionsPageComponent],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Insights</h1>

      <div class="flex gap-1 border-b border-[var(--xp-border)] text-sm">
        @for (t of tabs; track t.id) {
          <button
            type="button"
            class="px-3 py-2"
            [class.bg-[var(--xp-blue)]="tab() === t.id"
            [class.text-white]="tab() === t.id"
            (click)="setTab(t.id)"
          >
            {{ t.label }}
          </button>
        }
      </div>

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

  readonly tab = signal<InsightsTab>('overview');
  readonly tabs = [
    { id: 'overview' as const, label: 'Overview' },
    { id: 'reports' as const, label: 'Reports' },
    { id: 'predictions' as const, label: 'Predictions' },
  ];

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      const t = params.get('tab');
      if (t === 'reports' || t === 'predictions') {
        this.tab.set(t);
      } else {
        this.tab.set('overview');
      }
    });
  }

  setTab(id: InsightsTab): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id === 'overview' ? null : id },
      queryParamsHandling: 'merge',
    });
  }
}
