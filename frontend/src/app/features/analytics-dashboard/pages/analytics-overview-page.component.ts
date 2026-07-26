import { Component, OnInit, inject, signal } from '@angular/core';
import { DashboardService } from '../../dashboard/services/dashboard.service';
import { NotificationsWidgetComponent } from '../../dashboard/widgets/notifications-widget.component';
import { RunningWidgetComponent } from '../../dashboard/widgets/running-widget.component';
import { SyncWidgetComponent } from '../../dashboard/widgets/sync-widget.component';
import { AnalyticsDashboardService } from '../services/analytics-dashboard.service';
import { AnalyticsOverview } from '../models/analytics-dashboard.models';
import { KpiCardComponent } from '../widgets/kpi-card.component';
import { WidgetFrameComponent } from '../widgets/widget-frame.component';

@Component({
  selector: 'app-analytics-overview-page',
  standalone: true,
  imports: [
    RunningWidgetComponent,
    SyncWidgetComponent,
    NotificationsWidgetComponent,
    KpiCardComponent,
    WidgetFrameComponent,
  ],
  template: `
    <div class="space-y-6">
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <app-running-widget
          [loading]="dashboard.loading()"
          [progress]="dashboard.summary()?.running_progress ?? null"
        />
        <app-sync-widget
          [loading]="dashboard.loading()"
          [syncStatus]="dashboard.summary()?.sync_status ?? 'synced'"
          [pendingCount]="dashboard.summary()?.pending_sync_count ?? 0"
        />
        <app-notifications-widget
          [loading]="dashboard.loading()"
          [notifications]="dashboard.summary()?.notifications ?? []"
        />
      </div>

      @if (loading()) {
        <p class="text-sm text-[var(--text-muted)]">Loading overview…</p>
      } @else if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      } @else if (data()) {
        <div class="space-y-4">
          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            @for (kpi of data()!.kpis; track kpi.id) {
              <app-kpi-card
                [title]="kpi.title"
                [value]="kpi.value"
                [unit]="kpi.unit ?? null"
                [subtitle]="kpi.subtitle ?? null"
              />
            }
          </div>

          <div class="grid gap-3 lg:grid-cols-2">
            <app-widget-frame title="Upcoming Events">
              @if (!data()!.upcoming_events.length) {
                <p class="text-sm text-[var(--text-muted)]">No upcoming events</p>
              } @else {
                <ul class="space-y-2 text-sm">
                  @for (e of data()!.upcoming_events; track $index) {
                    <li class="flex justify-between gap-2">
                      <span>{{ e['title'] }}</span>
                      <span class="text-[var(--text-muted)]">{{ e['starts_at'] }}</span>
                    </li>
                  }
                </ul>
              }
            </app-widget-frame>

            <app-widget-frame title="Recent Activity">
              @if (!data()!.recent_activity.length) {
                <p class="text-sm text-[var(--text-muted)]">No recent activity</p>
              } @else {
                <ul class="space-y-2 text-sm">
                  @for (a of data()!.recent_activity; track $index) {
                    <li class="flex justify-between gap-2">
                      <span>{{ a['title'] }}</span>
                      <span class="text-[var(--text-muted)]">{{ a['module'] }}</span>
                    </li>
                  }
                </ul>
              }
            </app-widget-frame>
          </div>
        </div>
      }
    </div>
  `,
})
export class AnalyticsOverviewPageComponent implements OnInit {
  private readonly api = inject(AnalyticsDashboardService);
  readonly dashboard = inject(DashboardService);
  readonly data = signal<AnalyticsOverview | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.dashboard.getSummary().subscribe();
    this.api.overview().subscribe({
      next: (d) => {
        this.data.set(d);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load overview');
        this.loading.set(false);
      },
    });
  }
}
