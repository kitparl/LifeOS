import { DatePipe } from '@angular/common';
import {
  Component,
  ElementRef,
  HostListener,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { Subscription, filter, finalize } from 'rxjs';
import { Notification } from '../../features/notifications/models/notification.models';
import { NotificationsService } from '../../features/notifications/services/notifications.service';

interface ModuleStyle {
  icon: string;
  color: string;
  soft: string;
}

const MODULE_STYLES: Record<string, ModuleStyle> = {
  tasks: { icon: 'list-todo', color: 'var(--primary)', soft: 'var(--primary-soft)' },
  habits: { icon: 'flame', color: 'var(--warning)', soft: 'var(--warning-soft)' },
  finance: { icon: 'wallet', color: 'var(--success)', soft: 'var(--success-soft)' },
  calendar: { icon: 'calendar-days', color: 'var(--primary)', soft: 'var(--primary-soft)' },
  communication: { icon: 'message-square', color: 'var(--primary)', soft: 'var(--primary-soft)' },
  running: { icon: 'footprints', color: 'var(--success)', soft: 'var(--success-soft)' },
  journal: { icon: 'book-open', color: 'var(--text-muted)', soft: 'var(--surface-3)' },
  knowledge_notes: { icon: 'notebook-pen', color: 'var(--primary)', soft: 'var(--primary-soft)' },
  qa: { icon: 'circle-help', color: 'var(--text-muted)', soft: 'var(--surface-3)' },
};

const FALLBACK_STYLE: ModuleStyle = {
  icon: 'bell',
  color: 'var(--text-muted)',
  soft: 'var(--surface-3)',
};

const PREVIEW_LIMIT = 8;
const POLL_MS = 60_000;

@Component({
  selector: 'app-notification-dropdown',
  standalone: true,
  imports: [DatePipe, LucideDynamicIcon],
  host: {
    class: 'notif-host',
  },
  template: `
    <div
      class="notif-wrap"
      (mouseenter)="onWrapEnter()"
      (mouseleave)="onWrapLeave()"
    >
      <button
        type="button"
        class="btn-ghost notif-bell"
        data-testid="notification-bell"
        aria-label="Notifications"
        aria-haspopup="true"
        [attr.aria-expanded]="open()"
        (click)="onBellClick($event)"
      >
        <svg class="notif-bell__icon" lucideIcon="bell" aria-hidden="true"></svg>
        @if (unreadCount() > 0) {
          <span class="notif-badge" data-testid="notification-badge">{{ badgeLabel() }}</span>
        }
      </button>

      @if (open()) {
        <div
          class="notif-panel"
          role="menu"
          aria-label="Notifications"
          data-testid="notification-panel"
          (click)="$event.stopPropagation()"
        >
          <div class="notif-panel__card">
          <div class="notif-panel__header">
            <span class="notif-panel__title">Notifications</span>
            @if (unreadCount() > 0) {
              <button
                type="button"
                class="btn-ghost notif-panel__mark-all"
                data-testid="notification-mark-all"
                (click)="markAllRead($event)"
              >
                Mark all as read
              </button>
            }
          </div>

          <div class="notif-panel__body">
            @if (loading()) {
              <p class="notif-empty">Loading…</p>
            } @else if (items().length === 0) {
              <p class="notif-empty" data-testid="notification-empty">No notifications</p>
            } @else {
              <ul class="notif-list">
                @for (n of items(); track n.id) {
                  <li>
                    <button
                      type="button"
                      class="notif-row"
                      [class.notif-row--read]="n.is_read"
                      role="menuitem"
                      (click)="onRowClick(n, $event)"
                    >
                      <span
                        class="notif-row__icon"
                        [style.background]="moduleStyle(n.module).soft"
                        [style.color]="moduleStyle(n.module).color"
                      >
                        <svg
                          class="notif-row__icon-svg"
                          [lucideIcon]="moduleStyle(n.module).icon"
                          aria-hidden="true"
                        ></svg>
                      </span>
                      <span class="notif-row__text">
                        <span class="notif-row__message">{{ n.message }}</span>
                        <span class="notif-row__date">{{ n.created_at | date: 'short' }}</span>
                      </span>
                    </button>
                  </li>
                }
              </ul>
            }
          </div>

          <div class="notif-panel__footer">
            <button
              type="button"
              class="notif-more"
              data-testid="notification-more"
              (click)="goToInbox($event)"
            >
              More
            </button>
          </div>
          </div>
        </div>
      }
    </div>

    <style>
      :host,
      .notif-host {
        display: inline-flex;
        flex-shrink: 0;
        align-items: center;
        vertical-align: middle;
      }
      .notif-wrap {
        position: relative;
        display: inline-flex;
        align-items: center;
      }
      .notif-bell {
        position: relative;
        display: inline-flex !important;
        align-items: center;
        justify-content: center;
        padding: 0.35rem 0.5rem !important;
        min-height: 32px !important;
        min-width: 32px;
      }
      .notif-bell__icon {
        width: 1.1rem;
        height: 1.1rem;
        color: var(--text-muted);
        stroke: currentColor;
      }
      .notif-badge {
        position: absolute;
        top: 2px;
        right: 2px;
        min-width: 1rem;
        height: 1rem;
        padding: 0 3px;
        border-radius: 999px;
        background: var(--danger);
        color: #fff;
        font-size: 0.625rem;
        font-weight: 700;
        line-height: 1rem;
        text-align: center;
        pointer-events: none;
      }
      .notif-panel {
        position: absolute;
        top: 100%;
        right: 0;
        z-index: 60;
        width: 280px;
        max-width: min(280px, calc(100vw - 1rem));
        /* Invisible bridge so pointer can move from bell → panel without closing */
        padding-top: 6px;
        margin-top: -2px;
      }
      @media (max-width: 640px) {
        /* Parent column uses overflow:hidden; keep the flyout on-screen on phones */
        .notif-panel {
          position: fixed;
          top: 48px;
          right: 0.5rem;
          left: auto;
          margin-top: 0;
          padding-top: 0;
          width: min(280px, calc(100vw - 1rem));
          max-width: calc(100vw - 1rem);
        }
      }
      .notif-panel__card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        box-shadow: var(--shadow-md);
        overflow: hidden;
      }
      .notif-panel__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid var(--border);
      }
      .notif-panel__title {
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--text);
      }
      .notif-panel__mark-all {
        font-size: 0.6875rem !important;
        padding: 0.15rem 0.35rem !important;
        min-height: auto !important;
        color: var(--text-muted) !important;
      }
      .notif-panel__body {
        max-height: 280px;
        overflow-y: auto;
      }
      .notif-empty {
        margin: 0;
        padding: 1.25rem 0.75rem;
        text-align: center;
        font-size: 0.8125rem;
        color: var(--text-muted);
      }
      .notif-list {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .notif-row {
        display: flex;
        align-items: flex-start;
        gap: 0.625rem;
        width: 100%;
        padding: 0.55rem 0.75rem;
        border: none;
        border-bottom: 1px solid var(--border);
        background: transparent;
        text-align: left;
        cursor: pointer;
        color: var(--text);
      }
      .notif-row:last-child {
        border-bottom: none;
      }
      .notif-row:hover {
        background: var(--surface-2);
      }
      .notif-row--read {
        opacity: 0.65;
      }
      .notif-row--read .notif-row__message {
        font-weight: 400;
        color: var(--text-muted);
      }
      .notif-row__icon {
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.75rem;
        height: 1.75rem;
        border-radius: 999px;
      }
      .notif-row__icon-svg {
        width: 0.9rem;
        height: 0.9rem;
        stroke: currentColor;
      }
      .notif-row__text {
        min-width: 0;
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
      }
      .notif-row__message {
        font-size: 0.8125rem;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3;
      }
      .notif-row__date {
        font-size: 0.6875rem;
        color: var(--text-faint);
      }
      .notif-panel__footer {
        border-top: 1px solid var(--border);
        padding: 0.35rem 0.5rem;
      }
      .notif-more {
        display: block;
        width: 100%;
        padding: 0.4rem;
        border: none;
        border-radius: 4px;
        background: transparent;
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--primary);
        cursor: pointer;
        text-align: center;
      }
      .notif-more:hover {
        background: var(--primary-soft);
      }
    </style>
  `,
})
export class NotificationDropdownComponent implements OnInit, OnDestroy {
  private readonly elementRef = inject(ElementRef<HTMLElement>);
  private readonly notifications = inject(NotificationsService);
  private readonly router = inject(Router);

  readonly open = signal(false);
  readonly unreadCount = signal(0);
  readonly items = signal<Notification[]>([]);
  readonly loading = signal(false);

  private leaveCloseTimer: ReturnType<typeof setTimeout> | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private routerSub: Subscription | null = null;

  ngOnInit(): void {
    this.refreshUnreadCount();
    this.pollTimer = setInterval(() => this.refreshUnreadCount(), POLL_MS);
    this.routerSub = this.router.events
      .pipe(filter((e) => e instanceof NavigationEnd))
      .subscribe(() => {
        this.close();
        this.refreshUnreadCount();
      });
  }

  ngOnDestroy(): void {
    this.clearLeaveTimer();
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.routerSub?.unsubscribe();
  }

  badgeLabel(): string {
    const n = this.unreadCount();
    return n > 9 ? '9+' : String(n);
  }

  moduleStyle(module: string | null): ModuleStyle {
    if (!module) return FALLBACK_STYLE;
    return MODULE_STYLES[module] ?? FALLBACK_STYLE;
  }

  /** Cancel a pending leave-close when the pointer returns to bell/panel. */
  onWrapEnter(): void {
    this.clearLeaveTimer();
  }

  /** Close shortly after the pointer leaves bell + panel (desktop). */
  onWrapLeave(): void {
    if (!this.open()) return;
    this.clearLeaveTimer();
    this.leaveCloseTimer = setTimeout(() => this.close(), 120);
  }

  onBellClick(event: Event): void {
    event.stopPropagation();
    this.clearLeaveTimer();
    if (this.open()) {
      this.close();
    } else {
      this.openPanel();
    }
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.open()) return;
    const target = event.target as Node | null;
    if (target && !this.elementRef.nativeElement.contains(target)) {
      this.close();
    }
  }

  @HostListener('document:keydown', ['$event'])
  onDocumentKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape' && this.open()) {
      event.preventDefault();
      this.close();
    }
  }

  onRowClick(n: Notification, event: Event): void {
    event.preventDefault();
    event.stopPropagation();
    const route = n.route;
    this.notifications.markRead(n.id).subscribe({
      next: () => {
        this.refreshUnreadCount();
        if (route) {
          this.close();
          void this.router.navigateByUrl(route);
        } else {
          this.loadPreview();
        }
      },
    });
  }

  markAllRead(event: Event): void {
    event.preventDefault();
    event.stopPropagation();
    this.notifications.markAllRead().subscribe({
      next: () => {
        this.unreadCount.set(0);
        this.loadPreview();
      },
    });
  }

  goToInbox(event: Event): void {
    event.preventDefault();
    event.stopPropagation();
    this.close();
    void this.router.navigateByUrl('/notifications');
  }

  private openPanel(): void {
    if (this.open()) return;
    this.open.set(true);
    this.loadPreview();
    this.refreshUnreadCount();
  }

  private close(): void {
    this.clearLeaveTimer();
    this.open.set(false);
  }

  private clearLeaveTimer(): void {
    if (this.leaveCloseTimer) {
      clearTimeout(this.leaveCloseTimer);
      this.leaveCloseTimer = null;
    }
  }

  private refreshUnreadCount(): void {
    this.notifications.list({ unreadOnly: true, limit: 1 }).subscribe({
      next: (result) => this.unreadCount.set(result.total),
      error: () => undefined,
    });
  }

  private loadPreview(): void {
    this.loading.set(true);
    this.notifications
      .list({ limit: PREVIEW_LIMIT })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (result) => this.items.set(result.items),
        error: () => this.items.set([]),
      });
  }
}
