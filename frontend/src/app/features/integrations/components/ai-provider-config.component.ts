import { DatePipe } from '@angular/common';
import { Component, Input, OnInit, computed, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';
import { SecretInputComponent } from '../../../shared/secret-input/secret-input.component';
import {
  AiModelItem,
  AiProviderConfigStatus,
  AiProviderConfigUpdate,
  IntegrationsService,
  apiErrorMessage,
} from '../services/integrations.service';

/** Where to create an API key for each provider (docs links only; model lists come from the API). */
const KEY_URLS: Record<string, string> = {
  openai: 'https://platform.openai.com/api-keys',
  anthropic: 'https://console.anthropic.com/settings/keys',
  gemini: 'https://aistudio.google.com/apikey',
  sarvam: 'https://dashboard.sarvam.ai/',
};

@Component({
  selector: 'app-ai-provider-config',
  standalone: true,
  imports: [FormsModule, SecretInputComponent, DatePipe],
  template: `
    <div class="panel text-sm" [attr.data-testid]="'ai-provider-' + provider">
      <div class="flex items-start justify-between gap-2">
        <div>
          <p class="font-medium">{{ displayName }}</p>
          <p class="text-gray-600 text-xs mt-1">{{ description }}</p>
        </div>
        @if (status()) {
          <span
            class="text-xs shrink-0"
            [style.color]="status()!.configured && status()!.enabled ? 'var(--success)' : 'var(--text-muted)'"
          >
            {{ statusLabel() }}
          </span>
        }
      </div>

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">How to connect</summary>
        <ol class="mt-2 list-decimal pl-4 space-y-1" style="color: var(--text-muted)">
          <li>
            Create an API key at
            <a [href]="keyUrl" target="_blank" rel="noopener noreferrer">{{ keyHost }}</a>.
          </li>
          <li>Paste the key below (encrypted at rest; never shown raw after save).</li>
          <li>Save. Available models load from {{ displayName }} automatically; use Refresh models to pick up new ones.</li>
          <li>Choose a default model, or assign models per use case under <strong>AI defaults &amp; use cases</strong>.</li>
        </ol>
      </details>

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">Credentials &amp; configuration</summary>
        <div class="mt-3 flex flex-col gap-2 max-w-xl">
          <div class="flex flex-col gap-1">
            <label class="form-label" [for]="provider + '-key'">API key</label>
            <app-secret-input
              [inputId]="provider + '-key'"
              [(ngModel)]="keyInput"
              [placeholder]="keyPlaceholder()"
              autocomplete="off"
              [attr.data-testid]="'ai-provider-' + provider + '-key-input'"
            />
            @if (status()?.configured && status()?.api_key_masked) {
              <p class="text-xs" style="color: var(--text-muted)">
                Configured: {{ status()!.api_key_masked }} (leave blank to keep)
              </p>
            }
          </div>

          <label class="flex items-center gap-2 text-xs mt-1">
            <input
              type="checkbox"
              [(ngModel)]="enabled"
              [attr.data-testid]="'ai-provider-' + provider + '-enabled-checkbox'"
            />
            Enable {{ displayName }}
          </label>

          <div class="flex flex-col gap-1">
            <label class="form-label" [for]="provider + '-model'">Default model</label>
            @if (!useCustomModel) {
              <select
                [id]="provider + '-model'"
                class="input-field"
                [(ngModel)]="selectedModel"
                [attr.data-testid]="'ai-provider-' + provider + '-model-select'"
              >
                <option value="">Automatic</option>
                @for (m of chatModels(); track m.model_id) {
                  <option [value]="m.model_id">{{ m.display_name }}</option>
                }
              </select>
            } @else {
              <input
                [id]="provider + '-model'"
                class="input-field"
                [(ngModel)]="customModel"
                placeholder="e.g. a model id released after the last refresh"
                maxlength="80"
                [attr.data-testid]="'ai-provider-' + provider + '-custom-model-input'"
              />
            }
            <label class="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                [(ngModel)]="useCustomModel"
                [attr.data-testid]="'ai-provider-' + provider + '-custom-model-checkbox'"
              />
              Use custom model id
            </label>
          </div>

          @if (status()?.supports_base_url) {
            <div class="flex flex-col gap-1">
              <label class="form-label" [for]="provider + '-base-url'">Base URL (optional)</label>
              <input
                [id]="provider + '-base-url'"
                class="input-field"
                [(ngModel)]="baseUrl"
                placeholder="https://api.openai.com/v1"
                [attr.data-testid]="'ai-provider-' + provider + '-base-url-input'"
              />
            </div>
          }

          <div class="flex flex-wrap gap-2 mt-2">
            <button
              type="button"
              class="btn-primary text-xs"
              [disabled]="busy()"
              (click)="save()"
              [attr.data-testid]="'ai-provider-' + provider + '-save-button'"
            >
              {{ busy() ? 'Saving…' : 'Save' }}
            </button>
            <button
              type="button"
              class="btn-primary text-xs"
              [disabled]="busy() || !status()?.configured"
              (click)="test()"
              [attr.data-testid]="'ai-provider-' + provider + '-test-button'"
            >
              Test connection
            </button>
            <button
              type="button"
              class="btn-primary text-xs"
              [disabled]="busy() || !status()?.configured"
              (click)="refreshModels()"
              [attr.data-testid]="'ai-provider-' + provider + '-refresh-button'"
            >
              Refresh models
            </button>
          </div>

          @if (message()) {
            <p class="text-xs mt-1" [style.color]="ok() ? 'var(--success)' : 'var(--danger)'">{{ message() }}</p>
          }
          @if (status(); as s) {
            <p class="text-xs" style="color: var(--text-muted)">
              @if (s.last_tested_at) {
                Last test: {{ s.last_tested_at | date: 'medium' }} ({{ s.last_test_ok ? 'ok' : 'failed' }}) ·
              }
              Models: {{ s.model_count }}
              @if (s.models_refreshed_at) {
                (refreshed {{ s.models_refreshed_at | date: 'medium' }})
              }
            </p>
          }
        </div>
      </details>
    </div>
  `,
})
export class AiProviderConfigComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);

  @Input({ required: true }) provider = '';
  @Input({ required: true }) displayName = '';
  @Input({ required: true }) description = '';

  readonly connectionsChanged = output<void>();

  readonly status = signal<AiProviderConfigStatus | null>(null);
  readonly models = signal<AiModelItem[]>([]);
  readonly chatModels = computed(() => this.models().filter((m) => m.capabilities.includes('chat')));
  readonly busy = signal(false);
  readonly message = signal<string | null>(null);
  readonly ok = signal(false);

  keyInput = '';
  enabled = false;
  selectedModel = '';
  useCustomModel = false;
  customModel = '';
  baseUrl = '';

  get keyUrl(): string {
    return KEY_URLS[this.provider] ?? '';
  }

  get keyHost(): string {
    return this.keyUrl.replace(/^https:\/\//, '').replace(/\/$/, '');
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.integrations.getAiProvider(this.provider).subscribe({
      next: (s) => this.applyStatus(s),
      error: (err) => this.fail(err, `Failed to load ${this.displayName} settings`),
    });
    this.loadModels();
  }

  loadModels(): void {
    this.integrations.listAiModels(this.provider).subscribe({
      next: (res) => {
        this.models.set(res.models);
        this.syncModelForm();
      },
      error: () => this.models.set([]),
    });
  }

  statusLabel(): string {
    const s = this.status();
    if (!s) return '';
    if (s.configured && s.enabled) return s.status === 'error' ? 'Connected (last check failed)' : 'Connected';
    if (s.configured) return 'Configured (disabled)';
    return 'Not configured';
  }

  keyPlaceholder(): string {
    const masked = this.status()?.api_key_masked;
    return masked ? `Saved: ${masked}` : `Paste ${this.displayName} API key`;
  }

  save(): void {
    const body: AiProviderConfigUpdate = { enabled: this.enabled };
    if (this.keyInput.trim()) body.api_key = this.keyInput.trim();
    const model = this.useCustomModel ? this.customModel.trim() : this.selectedModel;
    body.default_model = model || null;
    body.custom_model = this.useCustomModel;
    if (this.status()?.supports_base_url) body.base_url = this.baseUrl.trim() || null;

    this.run(this.integrations.saveAiProvider(this.provider, body), (s) => {
      this.applyStatus(s);
      this.loadModels();
      this.succeed(
        s.models_refresh_error
          ? `Saved, but refreshing models failed: ${s.models_refresh_error}`
          : `${this.displayName} settings saved`,
        !s.models_refresh_error,
      );
      this.connectionsChanged.emit();
    });
  }

  test(): void {
    this.run(this.integrations.testAiProvider(this.provider), (res) => {
      this.succeed(res.detail, res.ok);
      this.integrations.getAiProvider(this.provider).subscribe({ next: (s) => this.status.set(s) });
    });
  }

  refreshModels(): void {
    this.run(this.integrations.refreshAiModels(this.provider), (res) => {
      this.models.set(res.models);
      this.syncModelForm();
      this.succeed(`Loaded ${res.models.length} models`, true);
      this.integrations.getAiProvider(this.provider).subscribe({ next: (s) => this.status.set(s) });
    });
  }

  private applyStatus(s: AiProviderConfigStatus): void {
    this.status.set(s);
    this.enabled = s.enabled;
    this.baseUrl = s.base_url ?? '';
    this.keyInput = '';
    this.syncModelForm();
  }

  /** A saved default that is not in the cached list is shown as a custom id. */
  private syncModelForm(): void {
    const saved = this.status()?.default_model ?? '';
    const known = this.models().some((m) => m.model_id === saved);
    this.useCustomModel = !!saved && !known;
    this.selectedModel = known ? saved : '';
    this.customModel = this.useCustomModel ? saved : '';
  }

  private run<T>(request: Observable<T>, onSuccess: (value: T) => void): void {
    this.busy.set(true);
    this.message.set(null);
    request.subscribe({
      next: (value) => {
        this.busy.set(false);
        onSuccess(value);
      },
      error: (err) => {
        this.busy.set(false);
        this.fail(err, `${this.displayName} request failed`);
      },
    });
  }

  private succeed(text: string, ok: boolean): void {
    this.ok.set(ok);
    this.message.set(text);
  }

  private fail(err: unknown, fallback: string): void {
    this.ok.set(false);
    this.message.set(apiErrorMessage(err, fallback));
  }
}
