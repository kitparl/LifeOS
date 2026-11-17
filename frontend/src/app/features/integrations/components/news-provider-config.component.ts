import { Component, Input, OnInit, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { apiErrorMessage } from '../../../core/utils/http';
import { SecretInputComponent } from '../../../shared/secret-input/secret-input.component';
import {
  IntegrationsService,
  NewsProviderConfigStatus,
  NewsProviderConfigUpdate,
  NewsProviderKey,
} from '../services/integrations.service';

/** API-key card for a news provider (several keys, tried in order). `provider` is the backend id (e.g. `freenewsapi`), so a new source reuses this card. */
@Component({
  selector: 'app-news-provider-config',
  standalone: true,
  imports: [FormsModule, SecretInputComponent],
  host: { class: 'contents' },
  template: `
    <div [id]="provider" class="panel text-sm">
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
        <summary class="cursor-pointer font-medium">How to connect</summary>
        <ol class="mt-2 list-decimal pl-4 space-y-1" style="color: var(--text-muted)">
          <li>Create a free account at <strong>freenewsapi.ai</strong> and generate an API key (free tier: 3,000 requests/month).</li>
          <li>Paste it below, Add key, then Test connection.</li>
          <li>Add more keys as backups: when one runs out of quota or is rate limited, the next one is used automatically.</li>
          <li>The monthly quota is per FreeNewsAPI <strong>account</strong>, so backup keys only help if they come from different accounts.</li>
          <li>Keys have no expiry date; the monthly quota (renews on the 1st, UTC) is what runs out. Test connection refreshes each key's remaining quota.</li>
        </ol>
      </details>

      <details class="mt-3 text-xs" [open]="!config()?.configured">
        <summary class="cursor-pointer font-medium">API keys</summary>
        <div class="mt-3 flex flex-col gap-2">
          @if (config()?.keys?.length) {
            <ul class="flex flex-col gap-1" data-testid="news-provider-keys">
              @for (k of config()!.keys; track k.id; let i = $index) {
                <li class="flex items-center justify-between gap-2">
                  <span>
                    <span style="color: var(--text-muted)">{{ i + 1 }}.</span> {{ k.masked }}
                    <span [style.color]="k.state === 'ok' ? 'var(--success)' : 'var(--warning)'">· {{ keyStateLabel(k) }}</span>
                    @if (quotaLabel(k); as quota) {
                      <span class="block" style="color: var(--text-muted)">{{ quota }}</span>
                    }
                  </span>
                  <span class="flex shrink-0 gap-3">
                    <button
                      type="button"
                      class="text-xs"
                      style="color: var(--primary)"
                      [disabled]="busy()"
                      [attr.aria-label]="'Test key ' + k.masked"
                      data-testid="news-provider-key-test"
                      (click)="testKey(k)"
                    >
                      Test
                    </button>
                    <button type="button" class="text-xs" style="color: var(--danger)" [disabled]="busy()" (click)="removeKey(k)">
                      Remove
                    </button>
                  </span>
                </li>
              }
            </ul>
            <p class="text-xs" style="color: var(--text-muted)">Keys are tried in this order.</p>
          }
          <div class="flex flex-col gap-1">
            <label class="form-label" [for]="provider + '-key'">{{ config()?.keys?.length ? 'Add another key' : displayName + ' API key' }}</label>
            <app-secret-input [inputId]="provider + '-key'" [(ngModel)]="keyInput" [placeholder]="'Paste ' + displayName + ' API key'" autocomplete="off" />
          </div>
          @if (config()?.configured) {
            <label class="flex items-center gap-2 text-xs">
              <input type="checkbox" [(ngModel)]="enabled" (ngModelChange)="saveEnabled()" />
              Enable {{ displayName }}
            </label>
          }
          <div class="flex flex-wrap gap-2 mt-1">
            <button type="button" class="btn-primary text-xs" [disabled]="busy()" (click)="addKey()">
              {{ busy() ? 'Saving…' : 'Add key' }}
            </button>
            <button type="button" class="btn-primary text-xs" [disabled]="busy() || !config()?.configured" (click)="test()">
              Test connection
            </button>
          </div>
          @if (message()) {
            <p class="text-xs" [style.color]="ok() ? 'var(--success)' : 'var(--danger)'">{{ message() }}</p>
          }
          @if (config()?.last_tested_at) {
            <p class="text-xs" style="color: var(--text-muted)">Last test: {{ config()!.last_tested_at }}</p>
          }
        </div>
      </details>
    </div>
  `,
})
export class NewsProviderConfigComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);

  @Input({ required: true }) provider = '';
  @Input({ required: true }) displayName = '';
  @Input({ required: true }) description = '';

  readonly connectionsChanged = output<void>();

  readonly config = signal<NewsProviderConfigStatus | null>(null);
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
    return 'Not configured';
  }

  /** "2,500 of 3,000 requests left · renews 1 Dec 2026" (keys have no expiry date; the monthly quota is what runs out). */
  quotaLabel(key: NewsProviderKey): string | null {
    if (key.quota_remaining === null || key.quota_limit === null) return null;
    const renews = key.quota_renews_at ? ` · renews ${new Date(key.quota_renews_at).toLocaleDateString()}` : '';
    return `${key.quota_remaining.toLocaleString()} of ${key.quota_limit.toLocaleString()} requests left${renews}`;
  }

  keyStateLabel(key: NewsProviderKey): string {
    const until = key.retry_at ? ` until ${new Date(key.retry_at).toLocaleString()}` : '';
    switch (key.state) {
      case 'ok':
        return 'Active';
      case 'rate_limited':
        return `Rate limited${until}`;
      case 'quota_exhausted':
        return `Quota used up${until}`;
      case 'invalid':
        return 'Rejected by FreeNewsAPI';
    }
  }

  private apply(status: NewsProviderConfigStatus): void {
    this.config.set(status);
    this.enabled = status.enabled;
    this.keyInput = '';
  }

  private fail(err: unknown, fallback: string): void {
    this.ok.set(false);
    this.message.set(apiErrorMessage(err, fallback));
    this.busy.set(false);
  }

  load(): void {
    this.integrations.getNewsProvider(this.provider).subscribe({
      next: (status) => this.apply(status),
      error: (err) => this.fail(err, `Failed to load ${this.displayName} settings`),
    });
  }

  addKey(): void {
    const key = this.keyInput.trim();
    if (!key) {
      this.ok.set(false);
      this.message.set('Paste an API key first');
      return;
    }
    this.update({ api_key: key }, `${this.displayName} key added`, `Failed to add ${this.displayName} key`);
  }

  saveEnabled(): void {
    this.update({ enabled: this.enabled }, `${this.displayName} settings saved`, `Failed to save ${this.displayName} settings`);
  }

  private update(body: NewsProviderConfigUpdate, success: string, failure: string): void {
    this.busy.set(true);
    this.message.set(null);
    this.integrations.saveNewsProviderConfig(this.provider, body).subscribe({
      next: (status) => {
        this.apply(status);
        this.ok.set(true);
        this.message.set(success);
        this.busy.set(false);
        this.connectionsChanged.emit();
      },
      error: (err) => this.fail(err, failure),
    });
  }

  test(): void {
    this.busy.set(true);
    this.message.set(null);
    this.integrations.testNewsProvider(this.provider).subscribe({
      next: (res) => {
        this.ok.set(res.ok);
        this.message.set(res.detail);
        this.busy.set(false);
        this.load();
      },
      error: (err) => this.fail(err, `${this.displayName} test failed`),
    });
  }

  testKey(key: NewsProviderKey): void {
    this.busy.set(true);
    this.message.set(null);
    this.integrations.testNewsProviderKey(this.provider, key.id).subscribe({
      next: (res) => {
        this.ok.set(res.ok);
        this.message.set(res.detail);
        this.busy.set(false);
        this.load();
      },
      error: (err) => this.fail(err, `${key.masked} test failed`),
    });
  }

  removeKey(key: NewsProviderKey): void {
    this.busy.set(true);
    this.message.set(null);
    this.integrations.removeNewsProviderKey(this.provider, key.id).subscribe({
      next: (status) => {
        this.apply(status);
        this.ok.set(true);
        this.message.set(`${key.masked} removed`);
        this.busy.set(false);
        this.connectionsChanged.emit();
      },
      error: (err) => this.fail(err, `Failed to remove ${this.displayName} key`),
    });
  }
}
