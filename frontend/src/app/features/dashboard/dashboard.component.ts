import { Component, OnInit, inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { DashboardService } from './services/dashboard.service';
import { ActivityWidgetComponent } from './widgets/activity-widget.component';
import { CalendarWidgetComponent } from './widgets/calendar-widget.component';
import { GoalsWidgetComponent } from './widgets/goals-widget.component';
import { HabitsWidgetComponent } from './widgets/habits-widget.component';
import { NotificationsWidgetComponent } from './widgets/notifications-widget.component';
import { QuickActionsWidgetComponent } from './widgets/quick-actions-widget.component';
import { RunningWidgetComponent } from './widgets/running-widget.component';
import { SyncWidgetComponent } from './widgets/sync-widget.component';
import { TasksWidgetComponent } from './widgets/tasks-widget.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    TasksWidgetComponent,
    HabitsWidgetComponent,
    GoalsWidgetComponent,
    RunningWidgetComponent,
    CalendarWidgetComponent,
    NotificationsWidgetComponent,
    SyncWidgetComponent,
    ActivityWidgetComponent,
    QuickActionsWidgetComponent,
  ],
  template: `
    <div class="space-y-3">
      <header class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 class="text-lg font-semibold">
            @if (auth.user(); as user) {
              Welcome, {{ user.display_name }}
            } @else {
              Dashboard
            }
          </h1>
          <p class="text-xs text-gray-600">What should you focus on today?</p>
        </div>
        @if (dashboard.error()) {
          <p class="text-xs text-red-700">{{ dashboard.error() }}</p>
        }
      </header>

      <div
        class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3 auto-rows-fr"
      >
        <app-quick-actions-widget
          class="md:col-span-2 xl:col-span-3"
          [loading]="dashboard.loading()"
          [actions]="dashboard.summary()?.quick_actions ?? []"
        />
        <app-tasks-widget
          [loading]="dashboard.loading()"
          [tasks]="dashboard.summary()?.tasks_today ?? []"
        />
        <app-habits-widget
          [loading]="dashboard.loading()"
          [habits]="dashboard.summary()?.habits_today ?? []"
        />
        <app-goals-widget
          [loading]="dashboard.loading()"
          [goals]="dashboard.summary()?.goals_progress ?? []"
        />
        <app-running-widget
          [loading]="dashboard.loading()"
          [progress]="dashboard.summary()?.running_progress ?? null"
        />
        <app-calendar-widget
          [loading]="dashboard.loading()"
          [events]="dashboard.summary()?.calendar_preview ?? []"
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
        <app-activity-widget
          class="md:col-span-2"
          [loading]="dashboard.loading()"
          [activities]="dashboard.summary()?.recent_activity ?? []"
        />
      </div>
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  readonly auth = inject(AuthService);
  readonly dashboard = inject(DashboardService);

  ngOnInit(): void {
    this.dashboard.getSummary().subscribe();
  }
}
