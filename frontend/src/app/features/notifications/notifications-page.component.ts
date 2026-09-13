import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { Notification } from './models/notification.models';
import { NotificationsService } from './services/notifications.service';

@Component({
  selector: 'app-notifications-page',
  standalone: true,
  imports: [RouterLink, DatePipe, ListPaginatorComponent],
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
        <a routerLink="/settings" fragment="integrations" class="link">Settings</a>.
      </p>

      @if (loading) {
        <div class="empty-state"><div class="skeleton" style="width: 120px; height: 14px"></div></div>
      } @else if (total === 0) {
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
        <app-list-paginator
          [total]="total"
          [pageSize]="pageSize"
          [currentPage]="currentPage"
          (pageChange)="setPage($event)"
        />
      }
    </div>
  `,
})
export class NotificationsPageComponent implements OnInit {
  private readonly notificationsService = inject(NotificationsService);

  notifications: Notification[] = [];
  total = 0;
  loading = false;
  currentPage = 1;
  readonly pageSize = 25;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const offset = (this.currentPage - 1) * this.pageSize;
    this.notificationsService.list({ limit: this.pageSize, offset }).subscribe({
      next: (result) => {
        this.notifications = result.items;
        this.total = result.total;
        this.clampPage();
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  setPage(page: number): void {
    this.currentPage = page;
    this.load();
  }

  private clampPage(): void {
    const totalPages = Math.max(1, Math.ceil(this.total / this.pageSize));
    if (this.currentPage > totalPages) {
      this.currentPage = totalPages;
      this.load();
    }
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
