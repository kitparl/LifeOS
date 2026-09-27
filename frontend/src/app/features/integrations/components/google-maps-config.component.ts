import { Component, Input, OnInit, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { apiErrorMessage } from '../../../core/utils/http';
import { SecretInputComponent } from '../../../shared/secret-input/secret-input.component';
import { GoogleMapsConfigStatus, IntegrationsService } from '../services/integrations.service';

/**
 * Optional per-user Google Maps key for Travel (place names, search, routes, elevation).
 * Travel works without it; the key is stored encrypted and only ever used server-side.
 */
@Component({
  selector: 'app-google-maps-config',
  standalone: true,
  imports: [FormsModule, RouterLink, SecretInputComponent],
  host: { class: 'contents' },
  template: `
    <div id="google-maps" class="panel text-sm">
      <div class="flex items-start justify-between gap-2">
        <div>
          <p class="font-medium">{{ displayName }}</p>
          <p class="text-gray-600 text-xs mt-1">{{ description }}</p>
        </div>
        @if (config(); as c) {
          <span class="text-xs shrink-0" [style.color]="c.configured && c.enabled ? 'var(--success)' : 'var(--text-muted)'">
            {{ statusLabel() }}
          </span>
        }
      </div>

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">How to connect (and protect your bill)</summary>
        <ol class="mt-2 list-decimal pl-4 space-y-1" style="color: var(--text-muted)">
          <li>In Google Cloud, enable only: Geocoding API, Places API (New), Routes API, Elevation API.</li>
          <li>Create an API key. Restrict it to those four APIs, and to your server's IP address.</li>
          <li>Set a billing budget with alerts, and per-API daily quotas.</li>
          <li>Paste the key below, Save, then Test connection.</li>
          <li>
            Travel's <a routerLink="/travel/settings/usage" class="underline">Maps usage</a> screen adds an application-level
            safety budget on top — it does not replace Google Cloud billing controls.
          </li>
        </ol>
      </details>

      <details class="mt-3 text-xs" [open]="!config()?.configured">
        <summary class="cursor-pointer font-medium">API key</summary>
        <div class="mt-3 flex flex-col gap-2">
          <div class="flex flex-col gap-1">
            <label class="form-label" for="google-maps-key">Google Maps API key</label>
            <app-secret-input inputId="google-maps-key" [(ngModel)]="keyInput" [placeholder]="keyPlaceholder()" autocomplete="off" />
            @if (config()?.api_key_masked) {
              <p class="text-xs" style="color: var(--text-muted)">Configured: {{ config()!.api_key_masked }} (leave blank to keep)</p>
            }
          </div>
          @if (config()?.configured) {
            <label class="flex items-center gap-2 text-xs">
              <input type="checkbox" [(ngModel)]="enabled" />
              Enable Google Maps lookups
            </label>
          }
          <div class="flex flex-wrap gap-2 mt-1">
            <button type="button" class="btn-primary text-xs" [disabled]="busy()" (click)="save()">
              {{ busy() ? 'Saving…' : 'Save' }}
            </button>
            <button type="button" class="btn-primary text-xs" [disabled]="busy() || !config()?.configured" (click)="test()">
              Test connection
            </button>
            @if (config()?.configured) {
              <button type="button" class="text-xs" style="color: var(--danger)" [disabled]="busy()" (click)="remove()">
                Remove key
              </button>
            }
          </div>
          @if (message()) {
            <p class="text-xs" [style.color]="ok() ? 'var(--success)' : 'var(--danger)'">{{ message() }}</p>
          }
        </div>
      </details>
    </div>
  `,
})
export class GoogleMapsConfigComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);

  @Input({ required: true }) displayName = '';
  @Input({ required: true }) description = '';

  readonly connectionsChanged = output<void>();

  readonly config = signal<GoogleMapsConfigStatus | null>(null);
  readonly busy = signal(false);
  readonly message = signal<string | null>(null);
  readonly ok = signal(false);
  keyInput = '';
  enabled = false;

  ngOnInit(): void {
    this.load();
  }

  statusLabel(): string {
    const c = this.config();
    if (!c) return '';
    if (c.configured && c.enabled) return 'Connected';
    if (c.configured) return 'Configured (disabled)';
    return 'Not configured (Travel uses coordinates only)';
  }

  keyPlaceholder(): string {
    const masked = this.config()?.api_key_masked;
    return masked ? `Saved: ${masked}` : 'Paste Google Maps API key';
  }

  load(): void {
    this.integrations.getGoogleMaps().subscribe({
      next: (status) => this.apply(status),
      error: (err) => this.fail(err, 'Failed to load Google Maps settings'),
    });
  }

  save(): void {
    const key = this.keyInput.trim();
    if (!key && !this.config()?.configured) {
      this.ok.set(false);
      this.message.set('Paste an API key first');
      return;
    }
    this.busy.set(true);
    this.message.set(null);
    this.integrations.saveGoogleMapsConfig(key ? { api_key: key } : { enabled: this.enabled }).subscribe({
      next: (status) => {
        this.apply(status);
        this.succeed('Google Maps settings saved');
        this.connectionsChanged.emit();
      },
      error: (err) => this.fail(err, 'Failed to save Google Maps settings'),
    });
  }

  test(): void {
    this.busy.set(true);
    this.message.set(null);
    this.integrations.testGoogleMaps().subscribe({
      next: (res) => {
        this.ok.set(res.ok);
        this.message.set(res.detail);
        this.busy.set(false);
        this.load();
      },
      error: (err) => this.fail(err, 'Google Maps test failed'),
    });
  }

  remove(): void {
    const id = this.config()?.connection_id;
    if (!id) return;
    this.busy.set(true);
    this.integrations.remove(id).subscribe({
      next: () => {
        this.succeed('Google Maps key removed');
        this.connectionsChanged.emit();
        this.load();
      },
      error: (err) => this.fail(err, 'Failed to remove Google Maps key'),
    });
  }

  private apply(status: GoogleMapsConfigStatus): void {
    this.config.set(status);
    this.enabled = status.enabled;
    this.keyInput = '';
  }

  private succeed(text: string): void {
    this.ok.set(true);
    this.message.set(text);
    this.busy.set(false);
  }

  private fail(err: unknown, fallback: string): void {
    this.ok.set(false);
    this.message.set(apiErrorMessage(err, fallback));
    this.busy.set(false);
  }
}
