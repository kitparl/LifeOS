import { DatePipe } from '@angular/common';
import { Component, Input, OnChanges, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';
import { AiSettings, AiUseCase, AiUseCaseHistoryItem } from '../../ai/models/ai.models';
import { AiService } from '../../ai/services/ai.service';
import { IntegrationProvider } from '../services/integrations.service';
import { apiErrorMessage } from '../../../core/utils/http';

/** Select values: '' = automatic, `model|<provider>|<id>` = a model from the provider's list. */
const AUTOMATIC = '';
const MODEL_PREFIX = 'model|';

interface ProviderGroup {
  provider: string;
  models: string[];
}

@Component({
  selector: 'app-ai-settings',
  standalone: true,
  imports: [FormsModule, DatePipe],
  template: `
    <div class="panel text-sm" data-testid="ai-settings">
      <p class="font-medium">AI use cases</p>
      <p class="text-gray-600 text-xs mt-1">
        Pick the model each feature uses. Changes save immediately. To use a model that isn't listed, add its ID on the
        provider card above.
      </p>

      <ul class="mt-3 divide-y divide-[var(--xp-border)]">
        <!-- Track by object: a fresh server copy re-renders the row, resetting the select after an error. -->
        @for (uc of useCases(); track uc) {
          <li class="py-2" [attr.data-testid]="'ai-use-case-' + uc.use_case">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <label class="font-medium" [for]="'ai-uc-' + uc.use_case">{{ uc.display_name }}</label>
              <select
                [id]="'ai-uc-' + uc.use_case"
                class="input-field w-full sm:w-80"
                [ngModel]="valueFor(uc)"
                (ngModelChange)="onSelect(uc, $event)"
                [disabled]="busy() || !groupsFor(uc).length"
                [attr.data-testid]="'ai-use-case-' + uc.use_case + '-select'"
              >
                <option value="">{{ automaticLabel(uc) }}</option>
                @for (g of groupsFor(uc); track g.provider) {
                  <optgroup [label]="providerName(g.provider)">
                    @for (m of g.models; track m) {
                      <option [value]="modelValue(g.provider, m)">{{ m }}</option>
                    }
                  </optgroup>
                }
              </select>
            </div>

            @if (uc.current && !uc.current.available) {
              <p class="text-xs mt-1" style="color: var(--danger)">
                {{ providerName(uc.current.provider) }} is not connected. Choose another model or reconnect it above.
              </p>
            }

          </li>
        }
      </ul>

      @if (!hasConnectedProvider()) {
        <p class="text-xs mt-2" style="color: var(--text-muted)">Connect a provider above to choose models.</p>
      }

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">Advanced</summary>

        @if (settings(); as s) {
          <p class="form-label mt-3">Defaults</p>
          <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 max-w-3xl">
            <div class="flex flex-col gap-1">
              <label class="form-label" for="ai-default-provider">Default provider</label>
              <select
                id="ai-default-provider"
                class="input-field"
                [(ngModel)]="s.default_provider"
                data-testid="ai-settings-default-provider-select"
              >
                <option [ngValue]="null">Automatic</option>
                @for (p of providers; track p.provider) {
                  <option [ngValue]="p.provider">{{ p.display_name }}</option>
                }
              </select>
            </div>
            <div class="flex flex-col gap-1">
              <label class="form-label" for="ai-timeout">Timeout (seconds)</label>
              <input id="ai-timeout" class="input-field" type="number" min="10" max="300" [(ngModel)]="s.timeout_seconds" data-testid="ai-settings-timeout-input" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="form-label" for="ai-max-tokens">Max tokens</label>
              <input id="ai-max-tokens" class="input-field" type="number" min="256" max="8192" [(ngModel)]="s.max_tokens" data-testid="ai-settings-max-tokens-input" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="form-label" for="ai-temperature">Temperature</label>
              <input id="ai-temperature" class="input-field" type="number" min="0" max="1" step="0.1" [(ngModel)]="s.temperature" data-testid="ai-settings-temperature-input" />
            </div>
          </div>
          <button
            type="button"
            class="btn-primary text-xs mt-2"
            [disabled]="busy()"
            (click)="saveSettings()"
            data-testid="ai-settings-save-button"
          >
            Save defaults
          </button>
        }

        <p class="form-label mt-4">Change history</p>
        <select
          class="input-field w-full sm:w-80"
          [ngModel]="historyUseCase()"
          (ngModelChange)="loadHistory($event)"
          aria-label="Use case history"
          data-testid="ai-settings-history-select"
        >
          <option value="">Select a use case…</option>
          @for (uc of useCases(); track uc.use_case) {
            <option [value]="uc.use_case">{{ uc.display_name }}</option>
          }
        </select>
        @if (history(); as rows) {
          <ul class="mt-2 pl-4 list-disc" style="color: var(--text-muted)">
            @for (h of rows; track h.effective_from) {
              <li>
                {{ providerName(h.provider) }} · {{ h.model }} — {{ h.effective_from | date: 'medium' }}
                {{ h.effective_to ? 'to ' + (h.effective_to | date: 'medium') : '(current)' }}
              </li>
            } @empty {
              <li>No changes yet (using automatic).</li>
            }
          </ul>
        }
      </details>

      @if (message()) {
        <p class="text-xs mt-2" [style.color]="ok() ? 'var(--success)' : 'var(--danger)'">{{ message() }}</p>
      }
    </div>
  `,
})
export class AiSettingsComponent implements OnChanges {
  private readonly ai = inject(AiService);

  /** AI providers from the Integrations catalog (group === 'ai'). */
  @Input({ required: true }) providers: IntegrationProvider[] = [];
  /** Bumped by the page when a provider card changes, so options reload. */
  @Input() reloadKey = 0;

  readonly settings = signal<AiSettings | null>(null);
  readonly useCases = signal<AiUseCase[]>([]);
  readonly historyUseCase = signal('');
  readonly history = signal<AiUseCaseHistoryItem[] | null>(null);
  readonly busy = signal(false);
  readonly message = signal<string | null>(null);
  readonly ok = signal(false);

  ngOnChanges(): void {
    this.ai.getSettings().subscribe({
      next: (s) => this.settings.set({ ...s }),
      error: (err) => this.fail(err, 'Failed to load AI defaults'),
    });
    this.reloadUseCases();
  }

  providerName(provider: string): string {
    return this.providers.find((p) => p.provider === provider)?.display_name ?? provider;
  }

  hasConnectedProvider(): boolean {
    return this.useCases().some((uc) => uc.options.length > 0);
  }

  modelValue(provider: string, model: string): string {
    return `${MODEL_PREFIX}${provider}|${model}`;
  }

  /** Explicit selections map to their option; no selection maps to "Automatic". */
  valueFor(uc: AiUseCase): string {
    const cur = uc.current;
    return cur?.updated_at ? this.modelValue(cur.provider, cur.model) : AUTOMATIC;
  }

  automaticLabel(uc: AiUseCase): string {
    const cur = uc.current;
    if (cur && !cur.updated_at) return `Automatic (${this.providerName(cur.provider)} · ${cur.model})`;
    return 'Automatic';
  }

  /** Listed models grouped by provider, plus a saved model that is no longer listed. */
  groupsFor(uc: AiUseCase): ProviderGroup[] {
    const groups = new Map<string, string[]>();
    for (const o of uc.options) {
      groups.set(o.provider, [...(groups.get(o.provider) ?? []), o.model]);
    }
    const cur = uc.current;
    if (cur?.updated_at && !groups.get(cur.provider)?.includes(cur.model)) {
      groups.set(cur.provider, [...(groups.get(cur.provider) ?? []), cur.model]);
    }
    return [...groups.entries()].map(([provider, models]) => ({ provider, models }));
  }

  onSelect(uc: AiUseCase, value: string): void {
    if (value === AUTOMATIC) {
      if (uc.current?.updated_at) {
        this.apply(this.ai.clearUseCaseModel(uc.use_case), `${uc.display_name} now uses the automatic model`);
      }
      return;
    }
    const [provider, ...rest] = value.slice(MODEL_PREFIX.length).split('|');
    const model = rest.join('|');
    this.apply(
      this.ai.setUseCaseModel(uc.use_case, { provider, model }),
      `${uc.display_name} now uses ${this.providerName(provider)} · ${model}`,
    );
  }

  saveSettings(): void {
    const s = this.settings();
    if (!s) return;
    this.busy.set(true);
    this.ai.saveSettings(s).subscribe({
      next: (saved) => {
        this.settings.set({ ...saved });
        this.busy.set(false);
        this.succeed('AI defaults saved');
        this.reloadUseCases();
      },
      error: (err) => {
        this.busy.set(false);
        this.fail(err, 'Failed to save AI defaults');
      },
    });
  }

  loadHistory(useCase: string): void {
    this.historyUseCase.set(useCase);
    this.history.set(null);
    if (!useCase) return;
    this.ai.useCaseHistory(useCase).subscribe({
      next: (rows) => this.history.set(rows),
      error: (err) => this.fail(err, 'Failed to load history'),
    });
  }

  private apply(request: Observable<AiUseCase>, successText: string): void {
    this.busy.set(true);
    this.message.set(null);
    request.subscribe({
      next: (updated) => {
        this.busy.set(false);
        this.useCases.update((list) => list.map((uc) => (uc.use_case === updated.use_case ? updated : uc)));
        this.succeed(successText);
        if (this.historyUseCase() === updated.use_case) this.loadHistory(updated.use_case);
      },
      error: (err) => {
        this.busy.set(false);
        this.fail(err, 'Failed to update model');
        // Server state is the source of truth; restore the select to it.
        this.reloadUseCases();
      },
    });
  }

  private reloadUseCases(): void {
    this.ai.listUseCases().subscribe({
      next: (cases) => this.useCases.set(cases),
      error: (err) => this.fail(err, 'Failed to load AI use cases'),
    });
  }

  private succeed(text: string): void {
    this.ok.set(true);
    this.message.set(text);
  }

  private fail(err: unknown, fallback: string): void {
    this.ok.set(false);
    this.message.set(apiErrorMessage(err, fallback));
  }
}
