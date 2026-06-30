import { DatePipe } from '@angular/common';
import { Component, Input, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NotificationsService } from '../../notifications/services/notifications.service';
import { NotificationItem } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-notifications-widget',
  standalone: true,
  imports: [DatePipe, RouterLink, WidgetSkeletonComponent],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0 flex items-center justify-between pr-2">
        <span>Notifications</span>
        <a routerLink="/notifications" class="text-xs font-normal underline">View all</a>
      </div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (notifications.length === 0) {
        <p class="p-3 text-sm text-gray-600">All caught up</p>
      } @else {
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (n of notifications; track n.id) {
            <li class="px-3 py-2" [class.opacity-60]="n.is_read">
              @if (n.route) {
                <a [routerLink]="n.route" class="text-[var(--xp-blue)] underline">{{ n.message }}</a>
              } @else {
                <p>{{ n.message }}</p>
              }
              <div class="mt-1 flex items-center justify-between gap-2">
                <p class="text-xs text-gray-500">{{ n.created_at | date: 'short' }}</p>
                @if (!n.is_read) {
                  <button type="button" class="text-xs underline" (click)="markRead(n.id)">Read</button>
                }
              </div>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class NotificationsWidgetComponent {
  private readonly notificationsService = inject(NotificationsService);

  @Input() loading = false;
  @Input() notifications: NotificationItem[] = [];

  markRead(id: string): void {
    this.notificationsService.markRead(id).subscribe();
  }
}
