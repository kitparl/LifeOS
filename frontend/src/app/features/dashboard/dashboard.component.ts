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
    <div class="space-y-4">
      <header class="panel flex flex-wrap items-center justify-between gap-3 !p-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--text-muted)]">Today</p>
          <h1 class="mt-1 text-xl font-semibold sm:text-2xl">
            @if (auth.user(); as user) {
              {{ user.display_name }}
            } @else {
              Quick Action
            }
          </h1>
          <p class="text-sm text-[var(--text-muted)]">Pick the next useful action, then move on.</p>
        </div>
        @if (dashboard.error()) {
          <p class="max-w-xl rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {{ dashboard.error() }}
          </p>
        }
      </header>

      <div class="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(20rem,0.65fr)]">
        <app-quick-actions-widget
          class="xl:row-span-2"
          [loading]="dashboard.loading()"
          [actions]="dashboard.summary()?.quick_actions ?? []"
        />
        <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
          <app-tasks-widget
            [loading]="dashboard.loading()"
            [tasks]="dashboard.summary()?.tasks_today ?? []"
          />
          <app-habits-widget
            [loading]="dashboard.loading()"
            [habits]="dashboard.summary()?.habits_today ?? []"
          />
        </div>
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <app-calendar-widget
          [loading]="dashboard.loading()"
          [events]="dashboard.summary()?.calendar_preview ?? []"
        />
        <app-notifications-widget
          [loading]="dashboard.loading()"
          [notifications]="dashboard.summary()?.notifications ?? []"
        />
      </div>

      <details class="panel group !p-0">
        <summary class="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
          <div>
            <p class="text-sm font-semibold">More signals</p>
            <p class="text-xs text-[var(--text-muted)]">Goals, running, sync, and recent activity when you need the detail.</p>
          </div>
          <span class="text-xs font-semibold text-[var(--xp-blue)] group-open:hidden">Show</span>
          <span class="hidden text-xs font-semibold text-[var(--xp-blue)] group-open:inline">Hide</span>
        </summary>
        <div class="grid gap-4 border-t border-[var(--xp-border)] p-4 md:grid-cols-2 xl:grid-cols-3">
          <app-goals-widget
            [loading]="dashboard.loading()"
            [goals]="dashboard.summary()?.goals_progress ?? []"
          />
          <app-running-widget
            [loading]="dashboard.loading()"
            [progress]="dashboard.summary()?.running_progress ?? null"
          />
          <app-sync-widget
            [loading]="dashboard.loading()"
            [syncStatus]="dashboard.summary()?.sync_status ?? 'synced'"
            [pendingCount]="dashboard.summary()?.pending_sync_count ?? 0"
          />
          <app-activity-widget
            class="md:col-span-2 xl:col-span-3"
            [loading]="dashboard.loading()"
            [activities]="dashboard.summary()?.recent_activity ?? []"
          />
        </div>
      </details>
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
