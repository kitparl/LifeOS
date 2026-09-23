import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  IntegrationConnection,
  IntegrationsService,
} from '../integrations/services/integrations.service';

/**
 * Central enable/disable entry point for integrations.
 * Secrets and advanced config stay on /integrations.
 */
@Component({
  selector: 'app-settings-integrations-section',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="panel max-w-2xl">
      <div class="space-y-3 text-sm">
        @if (loading()) {
          <p class="text-xs" style="color: var(--text-muted)">Loading…</p>
        } @else if (!connections().length) {
          <p class="text-xs" style="color: var(--text-muted)">
            No integrations connected yet.
            <a routerLink="/integrations" class="link">Set up Telegram</a>
          </p>
        } @else {
          <ul class="divide-y divide-[var(--xp-border)]">
            @for (c of connections(); track c.id) {
              <li class="flex flex-wrap items-center justify-between gap-2 py-2">
                <div>
                  <p class="font-medium capitalize">{{ c.display_name || c.provider }}</p>
                  <p class="text-xs" style="color: var(--text-muted)">
                    {{ c.enabled ? 'Enabled' : 'Disabled' }}
                    @if (c.status) {
                      · {{ c.status }}
                    }
                  </p>
                </div>
                <label class="toggle-switch gap-2 text-xs" [title]="c.enabled ? 'Turn off' : 'Turn on'">
                  <span style="color: var(--text-muted)">{{ c.enabled ? 'On' : 'Off' }}</span>
                  <input
                    type="checkbox"
                    [checked]="c.enabled"
                    [disabled]="busyId() === c.id"
                    [attr.aria-label]="'Enable ' + (c.display_name || c.provider)"
                    (change)="toggle(c, $event)"
                  />
                  <span class="toggle-switch__track" aria-hidden="true"></span>
                </label>
              </li>
            }
          </ul>
        }

        @if (message()) {
          <p class="text-xs" [style.color]="ok() ? 'var(--success)' : 'var(--danger)'">{{ message() }}</p>
        }

        <div class="flex flex-wrap items-center gap-x-3 gap-y-2 border-t border-[var(--xp-border)] pt-3">
          <a routerLink="/integrations" class="btn-secondary text-xs no-underline inline-block">
            Open Integrations hub
          </a>
          <span class="text-xs" style="color: var(--text-muted)">
            Your inbox stays at <a routerLink="/notifications" class="link">Notifications</a>.
          </span>
        </div>
      </div>
    </div>
  `,
})
export class SettingsIntegrationsSectionComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);

  readonly connections = signal<IntegrationConnection[]>([]);
  readonly loading = signal(false);
  readonly busyId = signal<string | null>(null);
  readonly message = signal<string | null>(null);
  readonly ok = signal(false);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.integrations.list().subscribe({
      next: (list) => {
        this.connections.set(list);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  toggle(conn: IntegrationConnection, event: Event): void {
    const enabled = (event.target as HTMLInputElement).checked;
    this.busyId.set(conn.id);
    this.message.set(null);
    this.integrations.toggle(conn.id, enabled).subscribe({
      next: (updated) => {
        this.connections.update((list) =>
          list.map((c) => (c.id === updated.id ? updated : c)),
        );
        this.busyId.set(null);
        this.ok.set(true);
        this.message.set(`${updated.display_name || updated.provider} ${enabled ? 'enabled' : 'disabled'}.`);
      },
      error: (err) => {
        this.busyId.set(null);
        this.ok.set(false);
        this.message.set(err?.error?.detail || 'Failed to update integration');
        // Revert checkbox by reloading
        this.load();
      },
    });
  }
}
