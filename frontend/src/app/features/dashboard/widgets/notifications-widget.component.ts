import { DatePipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { NotificationItem } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-notifications-widget',
  standalone: true,
  imports: [DatePipe, WidgetSkeletonComponent],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0">Notifications</div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (notifications.length === 0) {
        <p class="p-3 text-sm text-gray-600">All caught up</p>
      } @else {
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (n of notifications; track n.id) {
            <li class="px-3 py-2">
              <p>{{ n.message }}</p>
              <p class="text-xs text-gray-500">{{ n.created_at | date: 'short' }}</p>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class NotificationsWidgetComponent {
  @Input() loading = false;
  @Input() notifications: NotificationItem[] = [];
}
