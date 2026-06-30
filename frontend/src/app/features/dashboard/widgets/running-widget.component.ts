import { Component, Input } from '@angular/core';
import { RunningProgress } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-running-widget',
  standalone: true,
  imports: [WidgetSkeletonComponent],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0">Running Progress</div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (!progress) {
        <p class="p-3 text-sm text-gray-600">No runs logged</p>
      } @else {
        <div class="p-3 text-sm space-y-1">
          <p>Weekly: {{ progress.weekly_km }} / {{ progress.goal_km }} km</p>
          @if (progress.last_run) {
            <p class="text-xs text-gray-600">Last run: {{ progress.last_run }}</p>
          }
        </div>
      }
    </div>
  `,
})
export class RunningWidgetComponent {
  @Input() loading = false;
  @Input() progress: RunningProgress | null = null;
}
