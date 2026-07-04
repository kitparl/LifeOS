import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Notification } from './models/notification.models';
import { NotificationsService } from './services/notifications.service';

@Component({
  selector: 'app-notifications-page',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Notifications</h1>
        <div class="flex gap-2">
          <button type="button" class="btn-primary text-xs" (click)="markAllRead()">Mark all read</button>
        </div>
      </div>

      <p class="text-sm text-[var(--text-muted)]">
        Notification delivery settings are in
        <a routerLink="/settings" fragment="notifications" class="link">Settings</a>.
      </p>

      @if (loading) {
        <div class="empty-state"><div class="skeleton" style="width: 120px; height: 14px"></div></div>
      } @else if (notifications.length === 0) {
        <div class="empty-state">
          <p class="empty-state__title">All clear</p>
          <p class="empty-state__desc">No notifications right now.</p>
        </div>
      } @else {
        <ul class="panel !p-0 overflow-hidden text-sm">
          @for (n of notifications; track n.id) {
            <li class="flex items-start justify-between gap-2 px-3 py-2" [class.opacity-60]="n.is_read" style="border-bottom: 1px solid var(--border)">
              <div>
                @if (n.route) {
                  <a [routerLink]="n.route" class="link font-medium">{{ n.message }}</a>
                } @else {
                  <p>{{ n.message }}</p>
                }
                <p class="text-xs mt-0.5" style="color: var(--text-faint)">{{ n.created_at | date: 'medium' }}</p>
              </div>
              <div class="flex shrink-0 gap-2">
                @if (!n.is_read) {
                  <button type="button" class="btn-ghost text-xs" (click)="markRead(n.id)">Mark read</button>
                }
                <button type="button" class="btn-ghost text-xs" style="color: var(--danger)" (click)="remove(n.id)">Delete</button>
              </div>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class NotificationsPageComponent implements OnInit {
  private readonly notificationsService = inject(NotificationsService);

  notifications: Notification[] = [];
  loading = false;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.notificationsService.list().subscribe({
      next: (data) => {
        this.notifications = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  markRead(id: string): void {
    this.notificationsService.markRead(id).subscribe({ next: () => this.load() });
  }

  markAllRead(): void {
    this.notificationsService.markAllRead().subscribe({ next: () => this.load() });
  }

  remove(id: string): void {
    this.notificationsService.delete(id).subscribe({ next: () => this.load() });
  }
}
