import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { RunningProgress } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-running-widget',
  standalone: true,
  imports: [WidgetSkeletonComponent, RouterLink],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0 flex items-center justify-between pr-2">
        <span>Running Progress</span>
        <a routerLink="/running" class="text-[10px] font-normal underline">All</a>
      </div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (!progress) {
        <p class="p-3 text-sm text-gray-600">
          No runs logged.
          <a routerLink="/running/new" class="text-[var(--xp-blue)] underline">Log a run</a>
        </p>
      } @else {
        <div class="p-3 text-sm space-y-2">
          <p>Weekly: {{ progress.weekly_km }} / {{ progress.goal_km }} km</p>
          <div class="h-2 bg-gray-200 border border-[var(--xp-border)]">
            <div
              class="h-full bg-[var(--xp-blue)]"
              [style.width.%]="Math.min((progress.weekly_km / progress.goal_km) * 100, 100)"
            ></div>
          </div>
          @if (progress.last_run) {
            <p class="text-xs text-gray-600">Last run: {{ progress.last_run }}</p>
          }
          <a routerLink="/running/new" class="text-xs text-[var(--xp-blue)] underline">Log run</a>
        </div>
      }
    </div>
  `,
})
export class RunningWidgetComponent {
  readonly Math = Math;

  @Input() loading = false;
  @Input() progress: RunningProgress | null = null;
}
