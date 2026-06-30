import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Notification } from './models/notification.models';
import { NotificationsService } from './services/notifications.service';

@Component({
  selector: 'app-notifications-page',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Notifications</h1>
        <div class="flex gap-2">
          <button type="button" class="btn-primary text-xs" (click)="markAllRead()">Mark all read</button>
        </div>
      </div>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Telegram (optional)</div>
        <form class="space-y-2 p-3 text-sm" [formGroup]="settingsForm" (ngSubmit)="saveSettings()">
          <label class="flex items-center gap-2">
            <input type="checkbox" formControlName="telegram_enabled" />
            Enable Telegram notifications
          </label>
          <input class="input-field" formControlName="telegram_chat_id" placeholder="Telegram chat ID" />
          <button type="submit" class="btn-primary text-xs">Save settings</button>
        </form>
      </div>

      @if (loading) {
        <p class="text-sm text-gray-600">Loading…</p>
      } @else if (notifications.length === 0) {
        <p class="text-sm text-gray-600">No notifications.</p>
      } @else {
        <ul class="divide-y divide-[var(--xp-border)] panel !p-0 text-sm">
          @for (n of notifications; track n.id) {
            <li class="flex items-start justify-between gap-2 px-3 py-2" [class.opacity-60]="n.is_read">
              <div>
                @if (n.route) {
                  <a [routerLink]="n.route" class="font-medium text-[var(--xp-blue)] underline">{{ n.message }}</a>
                } @else {
                  <p>{{ n.message }}</p>
                }
                <p class="text-xs text-gray-500">{{ n.created_at | date: 'medium' }}</p>
              </div>
              <div class="flex shrink-0 gap-2">
                @if (!n.is_read) {
                  <button type="button" class="text-xs underline" (click)="markRead(n.id)">Read</button>
                }
                <button type="button" class="text-xs text-red-700" (click)="remove(n.id)">Delete</button>
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
  private readonly fb = inject(FormBuilder);

  notifications: Notification[] = [];
  loading = false;

  settingsForm = this.fb.nonNullable.group({
    telegram_enabled: [false],
    telegram_chat_id: [''],
  });

  ngOnInit(): void {
    this.load();
    this.notificationsService.getSettings().subscribe({
      next: (s) =>
        this.settingsForm.patchValue({
          telegram_enabled: s.telegram_enabled,
          telegram_chat_id: s.telegram_chat_id ?? '',
        }),
    });
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

  saveSettings(): void {
    const raw = this.settingsForm.getRawValue();
    this.notificationsService
      .updateSettings({
        telegram_enabled: raw.telegram_enabled,
        telegram_chat_id: raw.telegram_chat_id || null,
      })
      .subscribe();
  }
}
