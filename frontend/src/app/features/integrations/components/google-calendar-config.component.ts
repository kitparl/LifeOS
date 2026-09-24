import { DatePipe } from '@angular/common';
import { Component, Input, OnInit, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import {
  GoogleCalendarConfigStatus,
  GoogleCalendarSyncDirection,
  IntegrationsService,
} from '../services/integrations.service';

@Component({
  selector: 'app-google-calendar-config',
  standalone: true,
  imports: [FormsModule, DatePipe],
  host: { class: 'contents' },
  template: `
    <div class="panel text-sm">
      <div class="flex items-start justify-between gap-2">
        <div>
          <p class="font-medium">{{ displayName }}</p>
          <p class="text-gray-600 text-xs mt-1">{{ description }}</p>
        </div>
        @if (gcal()) {
          <span
            class="text-xs shrink-0"
            [style.color]="gcal()!.configured && gcal()!.enabled ? 'var(--success)' : 'var(--text-muted)'"
          >
            {{ statusLabel() }}
          </span>
        }
      </div>

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">How it works</summary>
        <ul class="mt-2 list-disc pl-4 space-y-1" style="color: var(--text-muted)">
          <li>Imports your primary Google Calendar (last 30 days, next 90 days) every 30 minutes, or on "Sync now".</li>
          <li><strong>Google → LifeOS</strong>: imported events are read-only here. Nothing is written to Google.</li>
          <li><strong>Two-way</strong>: edits and deletes of imported events are sent back to Google. Events you create in LifeOS stay in LifeOS.</li>
          <li>Disconnecting removes the imported events from LifeOS. Your Google Calendar is not changed.</li>
        </ul>
      </details>

      @if (gcal(); as g) {
        <div class="mt-3 flex flex-col gap-2">
          @if (!g.server_configured) {
            <p class="text-xs" style="color: var(--text-muted)">
              Not configured on the server (see GOOGLE_CALENDAR_SETUP.md).
            </p>
          }
          <div class="flex flex-col gap-1">
            <label class="form-label" for="gcal-direction">Sync direction</label>
            <select id="gcal-direction" class="input-field" [(ngModel)]="direction" [disabled]="busy()">
              <option value="google_to_lifeos">Google → LifeOS (recommended)</option>
              <option value="two_way">Two-way</option>
            </select>
          </div>
          @if (g.configured) {
            <label class="flex items-center gap-2 text-xs">
              <input type="checkbox" [(ngModel)]="enabled" [disabled]="busy()" />
              Enable Google Calendar sync
            </label>
            @if (direction === 'two_way' && !g.can_write) {
              <p class="text-xs" style="color: var(--danger)">
                Two-way needs write access. Click Reconnect to grant it. Until then nothing is written to Google.
              </p>
            }
          }
          <div class="flex flex-wrap gap-2 mt-1">
            @if (g.configured) {
              <button type="button" class="btn-primary text-xs" [disabled]="busy()" (click)="save()">Save</button>
              <button
                type="button"
                class="btn-primary text-xs"
                [disabled]="busy() || !g.enabled"
                (click)="syncNow()"
              >
                Sync now
              </button>
              <button
                type="button"
                class="btn-primary text-xs"
                [disabled]="busy() || !g.server_configured"
                (click)="connect()"
              >
                Reconnect
              </button>
              <button
                type="button"
                class="text-xs"
                style="color: var(--danger)"
                [disabled]="busy()"
                (click)="disconnect()"
              >
                Disconnect
              </button>
            } @else {
              <button
                type="button"
                class="btn-primary text-xs"
                [disabled]="busy() || !g.server_configured"
                (click)="connect()"
              >
                Connect
              </button>
            }
          </div>
          @if (message()) {
            <p class="text-xs" [style.color]="ok() ? 'var(--success)' : 'var(--danger)'">{{ message() }}</p>
          } @else if (g.last_sync_message) {
            <p class="text-xs" [style.color]="g.last_sync_ok === false ? 'var(--danger)' : 'var(--text-muted)'">
              {{ g.last_sync_message }}
            </p>
          }
          @if (g.last_sync_at) {
            <p class="text-xs" style="color: var(--text-muted)">Last sync: {{ g.last_sync_at | date: 'medium' }}</p>
          }
        </div>
      }
    </div>
  `,
})
export class GoogleCalendarConfigComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly confirmService = inject(ConfirmService);

  @Input({ required: true }) displayName = '';
  @Input({ required: true }) description = '';

  readonly connectionsChanged = output<void>();

  readonly gcal = signal<GoogleCalendarConfigStatus | null>(null);
  readonly busy = signal(false);
  readonly message = signal<string | null>(null);
  readonly ok = signal(false);
  direction: GoogleCalendarSyncDirection = 'google_to_lifeos';
  enabled = false;

  ngOnInit(): void {
    // Google redirects back to /integrations?code=…&state=… (or ?error=…).
    const params = this.route.snapshot.queryParamMap;
    const code = params.get('code');
    const state = params.get('state');
    const error = params.get('error');
    if (code && state) {
      this.clearQuery();
      this.completeOAuth(code, state);
    } else if (error && state) {
      this.clearQuery();
      this.fail(error === 'access_denied' ? 'Google access was not granted' : 'Google authorization failed');
      this.load();
    } else {
      this.load();
    }
  }

  private clearQuery(): void {
    this.router.navigate([], { relativeTo: this.route, queryParams: {}, replaceUrl: true });
  }

  private apply(status: GoogleCalendarConfigStatus): void {
    this.gcal.set(status);
    this.direction = status.sync_direction;
    this.enabled = status.enabled;
  }

  private fail(msg: string): void {
    this.ok.set(false);
    this.message.set(msg);
    this.busy.set(false);
  }

  load(): void {
    this.integrations.getGoogleCalendar().subscribe({
      next: (s) => this.apply(s),
      error: () => this.fail('Failed to load Google Calendar settings'),
    });
  }

  statusLabel(): string {
    const g = this.gcal();
    if (!g) return '';
    if (g.configured && g.status === 'error') return 'Error';
    if (g.configured && g.enabled) return 'Connected';
    if (g.configured) return 'Connected (disabled)';
    return 'Not connected';
  }

  connect(): void {
    this.busy.set(true);
    this.message.set(null);
    this.integrations.startGoogleCalendarOAuth(this.direction).subscribe({
      next: (res) => (window.location.href = res.auth_url),
      error: (err) => this.fail(err?.error?.detail || 'Could not start Google authorization'),
    });
  }

  private completeOAuth(code: string, state: string): void {
    this.busy.set(true);
    this.message.set('Connecting Google Calendar…');
    this.ok.set(true);
    this.integrations.completeGoogleCalendarOAuth(code, state).subscribe({
      next: (s) => {
        this.apply(s);
        this.ok.set(s.last_sync_ok !== false);
        this.message.set(s.last_sync_message || 'Google Calendar connected');
        this.busy.set(false);
        this.connectionsChanged.emit();
      },
      error: (err) => {
        this.fail(err?.error?.detail || 'Could not connect Google Calendar');
        this.load();
      },
    });
  }

  save(): void {
    this.busy.set(true);
    this.message.set(null);
    this.integrations
      .saveGoogleCalendarConfig({ enabled: this.enabled, sync_direction: this.direction })
      .subscribe({
        next: (s) => {
          this.apply(s);
          this.ok.set(true);
          this.message.set('Google Calendar settings saved');
          this.busy.set(false);
          this.connectionsChanged.emit();
        },
        error: (err) => this.fail(err?.error?.detail || 'Failed to save Google Calendar settings'),
      });
  }

  syncNow(): void {
    this.busy.set(true);
    this.message.set(null);
    this.integrations.syncGoogleCalendar().subscribe({
      next: (res) => {
        this.ok.set(res.status === 'synced');
        this.message.set(res.message);
        this.busy.set(false);
        this.load();
      },
      error: (err) => this.fail(err?.error?.detail || 'Sync failed'),
    });
  }

  async disconnect(): Promise<void> {
    const confirmed = await this.confirmService.confirm(
      'Disconnect Google Calendar? Imported events will be removed from LifeOS. Your Google Calendar is not changed.',
      'Disconnect Google Calendar',
    );
    if (!confirmed) return;
    this.busy.set(true);
    this.message.set(null);
    this.integrations.disconnectGoogleCalendar().subscribe({
      next: () => {
        this.ok.set(true);
        this.message.set('Google Calendar disconnected');
        this.busy.set(false);
        this.load();
        this.connectionsChanged.emit();
      },
      error: (err) => this.fail(err?.error?.detail || 'Failed to disconnect'),
    });
  }
}
