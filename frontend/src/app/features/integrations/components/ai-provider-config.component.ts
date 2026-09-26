import { DatePipe } from '@angular/common';
import { Component, Input, OnInit, computed, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';
import { SecretInputComponent } from '../../../shared/secret-input/secret-input.component';
import {
  AiModelItem,
  AiModelsResponse,
  AiProviderConfigStatus,
  AiProviderConfigUpdate,
  IntegrationsService,
} from '../services/integrations.service';
import { apiErrorMessage } from '../../../core/utils/http';

/** Where to create an API key for each provider (docs links only; model lists come from the API). */
const KEY_URLS: Record<string, string> = {
  openai: 'https://platform.openai.com/api-keys',
  anthropic: 'https://console.anthropic.com/settings/keys',
  gemini: 'https://aistudio.google.com/apikey',
  sarvam: 'https://dashboard.sarvam.ai/',
  mistral: 'https://console.mistral.ai/api-keys',
  groq: 'https://console.groq.com/keys',
  xai: 'https://console.x.ai/',
  deepseek: 'https://platform.deepseek.com/api_keys',
  together: 'https://api.together.ai/settings/api-keys',
  openrouter: 'https://openrouter.ai/settings/keys',
  perplexity: 'https://www.perplexity.ai/settings/api',
};

/** Show a filter box once the list gets long (OpenRouter can return hundreds of models). */
const FILTER_THRESHOLD = 8;

type TestResult = { ok: boolean; detail: string } | 'pending';

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
          <li>
            @if (status()?.supports_model_listing !== false) {
              Save. Your account's models load automatically; use Fetch from API to pick up new ones, or add a model ID by hand.
            } @else {
              Save. {{ displayName }} has no model-list API, so suggested model IDs are added; add any other ID by hand.
            }
          </li>
          <li>Use Test on a model to confirm your key can call it, then assign models under <strong>AI use cases</strong>.</li>
        </ol>
      </details>

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">Credentials &amp; models</summary>
        <div class="mt-3 flex flex-col gap-3 max-w-xl">
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

          <label class="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              [(ngModel)]="enabled"
              [attr.data-testid]="'ai-provider-' + provider + '-enabled-checkbox'"
            />
            Enable {{ displayName }}
          </label>

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

          <!-- Models: fetched from the provider's API and/or added by hand -->
          <div class="flex flex-col gap-2" [attr.data-testid]="'ai-provider-' + provider + '-models'">
            <div class="flex items-center justify-between gap-2">
              <p class="form-label">Models ({{ models().length }})</p>
              @if (status()?.supports_model_listing !== false) {
                <button
                  type="button"
                  class="btn-secondary text-xs"
                  [disabled]="busy() || !status()?.configured"
                  (click)="refreshModels()"
                  [attr.data-testid]="'ai-provider-' + provider + '-refresh-button'"
                >
                  Fetch from API
                </button>
              } @else {
                <span style="color: var(--text-muted)">No model-list API</span>
              }
            </div>

            @if (models().length > filterThreshold) {
              <input
                class="input-field"
                type="search"
                placeholder="Filter models"
                [ngModel]="filter()"
                (ngModelChange)="filter.set($event)"
                [attr.aria-label]="'Filter ' + displayName + ' models'"
              />
            }

            @if (models().length) {
              <ul class="max-h-56 overflow-y-auto rounded border border-[var(--xp-border)] divide-y divide-[var(--xp-border)]">
                @for (m of visibleModels(); track m.model_id) {
                  <li class="flex flex-wrap items-center justify-between gap-2 px-2 py-1.5">
                    <div class="min-w-0">
                      <p class="break-all">{{ m.model_id }}</p>
                      <p style="color: var(--text-muted)">
                        {{ m.source === 'manual' ? 'added' : 'fetched' }}
                        @if (m.capabilities.includes('embedding')) {
                          · embedding
                        }
                        @if (testResults()[m.model_id]; as r) {
                          @if (r === 'pending') {
                            · testing…
                          } @else {
                            · <span [style.color]="r.ok ? 'var(--success)' : 'var(--danger)'">{{ r.ok ? '✓' : '✗' }} {{ r.detail }}</span>
                          }
                        }
                      </p>
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                      @if (!m.capabilities.includes('embedding')) {
                        <button
                          type="button"
                          class="text-xs link"
                          [disabled]="!status()?.configured || testResults()[m.model_id] === 'pending'"
                          (click)="testModel(m.model_id)"
                          [attr.data-testid]="'ai-provider-' + provider + '-test-model-' + m.model_id"
                        >
                          Test
                        </button>
                      }
                      @if (m.source === 'manual') {
                        <button
                          type="button"
                          class="text-xs"
                          style="color: var(--danger)"
                          [attr.aria-label]="'Remove ' + m.model_id"
                          (click)="removeModel(m.model_id)"
                        >
                          ✕
                        </button>
                      }
                    </div>
                  </li>
                } @empty {
                  <li class="px-2 py-1.5" style="color: var(--text-muted)">No models match.</li>
                }
              </ul>
            } @else {
              <p style="color: var(--text-muted)">
                {{ status()?.supports_model_listing === false ? 'Add model IDs below.' : 'Save a key to load models, or add model IDs below.' }}
              </p>
            }

            <div class="flex flex-wrap items-center gap-2">
              <input
                class="input-field flex-1 min-w-0"
                [(ngModel)]="newModelId"
                maxlength="80"
                placeholder="Add model ID, e.g. a newly released model"
                [attr.aria-label]="'Add ' + displayName + ' model ID'"
                (keydown.enter)="addModel()"
                [attr.data-testid]="'ai-provider-' + provider + '-add-model-input'"
              />
              <button
                type="button"
                class="btn-secondary text-xs"
                [disabled]="busy() || !newModelId.trim()"
                (click)="addModel()"
                [attr.data-testid]="'ai-provider-' + provider + '-add-model-button'"
              >
                Add
              </button>
            </div>
          </div>

          <div class="flex flex-col gap-1">
            <label class="form-label" [for]="provider + '-model'">Default model</label>
            <select
              [id]="provider + '-model'"
              class="input-field"
              [(ngModel)]="selectedModel"
              [attr.data-testid]="'ai-provider-' + provider + '-model-select'"
            >
              <option value="">Automatic</option>
              @for (id of defaultModelOptions(); track id) {
                <option [value]="id">{{ id }}</option>
              }
            </select>
          </div>

          <div class="flex flex-wrap gap-2">
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
          </div>

          @if (message()) {
            <p class="text-xs" [style.color]="ok() ? 'var(--success)' : 'var(--danger)'">{{ message() }}</p>
          }
          @if (status(); as s) {
            <p class="text-xs" style="color: var(--text-muted)">
              @if (s.last_tested_at) {
                Last test: {{ s.last_tested_at | date: 'medium' }} ({{ s.last_test_ok ? 'ok' : 'failed' }}) ·
              }
              @if (s.models_refreshed_at) {
                Models updated {{ s.models_refreshed_at | date: 'medium' }}
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

  readonly filterThreshold = FILTER_THRESHOLD;
  readonly status = signal<AiProviderConfigStatus | null>(null);
  readonly models = signal<AiModelItem[]>([]);
  readonly filter = signal('');
  readonly testResults = signal<Record<string, TestResult>>({});
  readonly visibleModels = computed(() => {
    const q = this.filter().trim().toLowerCase();
    return q ? this.models().filter((m) => m.model_id.toLowerCase().includes(q)) : this.models();
  });
  /** Chat models, plus a saved default that is no longer listed (so saving never drops it). */
  readonly defaultModelOptions = computed(() => {
    const ids = this.models()
      .filter((m) => m.capabilities.includes('chat'))
      .map((m) => m.model_id);
    const saved = this.status()?.default_model;
    return saved && !ids.includes(saved) ? [...ids, saved] : ids;
  });
  readonly busy = signal(false);
  readonly message = signal<string | null>(null);
  readonly ok = signal(false);

  keyInput = '';
  enabled = false;
  selectedModel = '';
  baseUrl = '';
  newModelId = '';

  get keyUrl(): string {
    return KEY_URLS[this.provider] ?? '';
  }

  get keyHost(): string {
    return this.keyUrl.replace(/^https:\/\//, '').replace(/\/$/, '');
  }

  ngOnInit(): void {
    this.integrations.getAiProvider(this.provider).subscribe({
      next: (s) => this.applyStatus(s),
      error: (err) => this.fail(err, `Failed to load ${this.displayName} settings`),
    });
    this.loadModels();
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
    const body: AiProviderConfigUpdate = { enabled: this.enabled, default_model: this.selectedModel || null };
    if (this.keyInput.trim()) body.api_key = this.keyInput.trim();
    // A saved default that is no longer listed is kept as-is.
    const listed = this.models().some((m) => m.model_id === this.selectedModel);
    if (this.selectedModel && !listed) body.custom_model = true;
    if (this.status()?.supports_base_url) body.base_url = this.baseUrl.trim() || null;

    this.run(this.integrations.saveAiProvider(this.provider, body), (s) => {
      this.applyStatus(s);
      this.loadModels();
      this.succeed(
        s.models_refresh_error
          ? `Saved, but loading models failed: ${s.models_refresh_error}`
          : `${this.displayName} settings saved`,
        !s.models_refresh_error,
      );
      this.connectionsChanged.emit();
    });
  }

  test(): void {
    this.run(this.integrations.testAiProvider(this.provider), (res) => {
      this.succeed(res.detail, res.ok);
      this.reloadStatus();
    });
  }

  refreshModels(): void {
    this.run(this.integrations.refreshAiModels(this.provider), (res) => {
      this.applyModels(res);
      this.succeed(`Loaded ${res.models.length} models`, true);
      this.reloadStatus();
    });
  }

  addModel(): void {
    const modelId = this.newModelId.trim();
    if (!modelId) return;
    this.run(this.integrations.addAiModel(this.provider, modelId), (res) => {
      this.applyModels(res);
      this.newModelId = '';
      this.succeed(`Added ${modelId}`, true);
      this.connectionsChanged.emit();
    });
  }

  removeModel(modelId: string): void {
    this.run(this.integrations.removeAiModel(this.provider, modelId), (res) => {
      this.applyModels(res);
      this.succeed(`Removed ${modelId}`, true);
      this.connectionsChanged.emit();
    });
  }

  testModel(modelId: string): void {
    this.setTestResult(modelId, 'pending');
    this.integrations.testAiModel(this.provider, modelId).subscribe({
      next: (res) => this.setTestResult(modelId, { ok: res.ok, detail: res.detail }),
      error: (err) => this.setTestResult(modelId, { ok: false, detail: apiErrorMessage(err, 'Test failed') }),
    });
  }

  private loadModels(): void {
    this.integrations.listAiModels(this.provider).subscribe({
      next: (res) => this.applyModels(res),
      error: () => this.models.set([]),
    });
  }

  private reloadStatus(): void {
    this.integrations.getAiProvider(this.provider).subscribe({ next: (s) => this.status.set(s) });
  }

  private applyModels(res: AiModelsResponse): void {
    this.models.set(res.models);
  }

  private applyStatus(s: AiProviderConfigStatus): void {
    this.status.set(s);
    this.enabled = s.enabled;
    this.baseUrl = s.base_url ?? '';
    this.selectedModel = s.default_model ?? '';
    this.keyInput = '';
  }

  private setTestResult(modelId: string, result: TestResult): void {
    this.testResults.update((results) => ({ ...results, [modelId]: result }));
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
