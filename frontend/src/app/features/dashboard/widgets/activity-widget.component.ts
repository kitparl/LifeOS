import { DatePipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { ActivityItem } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-activity-widget',
  standalone: true,
  imports: [DatePipe, WidgetSkeletonComponent],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0">Recent Activity</div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (activities.length === 0) {
        <p class="p-3 text-sm text-gray-600">No recent activity</p>
      } @else {
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (a of activities; track a.at + a.label) {
            <li class="flex justify-between gap-2 px-3 py-2">
              <span>{{ a.label }}</span>
              <span class="text-xs text-gray-500">{{ a.at | date: 'short' }}</span>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class ActivityWidgetComponent {
  @Input() loading = false;
  @Input() activities: ActivityItem[] = [];
}
