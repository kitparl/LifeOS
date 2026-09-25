import { DatePipe } from '@angular/common';
import { Component, Input, OnChanges, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  AiModelOption,
  AiSettings,
  AiUseCase,
  AiUseCaseHistoryItem,
  AiUseCaseModelUpdate,
} from '../../ai/models/ai.models';
import { AiService } from '../../ai/services/ai.service';
import { IntegrationProvider, apiErrorMessage } from '../services/integrations.service';

interface UseCaseRow {
  useCase: AiUseCase;
  provider: string;
  model: string;
  custom: boolean;
  customModel: string;
  history: AiUseCaseHistoryItem[] | null;
}

@Component({
  selector: 'app-ai-settings',
  standalone: true,
  imports: [FormsModule, DatePipe],
  template: `
    <div class="panel text-sm" data-testid="ai-settings">
      <p class="font-medium">AI defaults &amp; use cases</p>
      <p class="text-gray-600 text-xs mt-1">
        Choose which model each LifeOS feature uses. Options come from the model lists of your connected providers.
      </p>

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">Defaults</summary>
        @if (settings(); as s) {
          <div class="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4 max-w-3xl">
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
      </details>

      <details class="mt-3 text-xs" open>
        <summary class="cursor-pointer font-medium">Use cases</summary>
        <ul class="mt-2 divide-y divide-[var(--xp-border)]">
          @for (row of rows(); track row.useCase.use_case) {
            <li class="py-2 flex flex-col gap-2" [attr.data-testid]="'ai-use-case-' + row.useCase.use_case">
              <div class="flex flex-wrap items-baseline justify-between gap-2">
                <p class="font-medium">{{ row.useCase.display_name }}</p>
                <p style="color: var(--text-muted)">
                  @if (row.useCase.current; as cur) {
                    Using {{ providerName(cur.provider) }} · {{ cur.model }}
                    {{ cur.updated_at ? '' : '(automatic)' }}
                    @if (!cur.available) {
                      <span style="color: var(--danger)">— provider not connected</span>
                    }
                  } @else {
                    No provider connected
                  }
                </p>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <select class="input-field" [(ngModel)]="row.provider" (ngModelChange)="row.model = ''" [attr.aria-label]="row.useCase.display_name + ' provider'">
                  <option value="">Provider…</option>
                  @for (p of rowProviders(row); track p) {
                    <option [value]="p">{{ providerName(p) }}</option>
                  }
                </select>
                @if (!row.custom) {
                  <select class="input-field" [(ngModel)]="row.model" [disabled]="!row.provider" [attr.aria-label]="row.useCase.display_name + ' model'">
                    <option value="">Model…</option>
                    @for (o of rowModels(row); track o.model) {
                      <option [value]="o.model">{{ o.model }}</option>
                    }
                  </select>
                } @else {
                  <input class="input-field" [(ngModel)]="row.customModel" maxlength="80" placeholder="Custom model id" [attr.aria-label]="row.useCase.display_name + ' custom model id'" />
                }
                <label class="flex items-center gap-1">
                  <input type="checkbox" [(ngModel)]="row.custom" />
                  Custom id
                </label>
                <button
                  type="button"
                  class="btn-primary text-xs"
                  [disabled]="busy() || !row.provider || !(row.custom ? row.customModel.trim() : row.model)"
                  (click)="assign(row)"
                  [attr.data-testid]="'ai-use-case-' + row.useCase.use_case + '-save-button'"
                >
                  Assign
                </button>
                <button type="button" class="text-xs link" (click)="toggleHistory(row)">
                  {{ row.history ? 'Hide history' : 'History' }}
                </button>
              </div>
              @if (row.history) {
                <ul class="pl-4 list-disc" style="color: var(--text-muted)">
                  @for (h of row.history; track h.effective_from) {
                    <li>
                      {{ providerName(h.provider) }} · {{ h.model }} — from {{ h.effective_from | date: 'medium' }}
                      {{ h.effective_to ? 'to ' + (h.effective_to | date: 'medium') : '(current)' }}
                    </li>
                  } @empty {
                    <li>No changes yet.</li>
                  }
                </ul>
              }
            </li>
          }
        </ul>
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
  readonly rows = signal<UseCaseRow[]>([]);
  readonly busy = signal(false);
  readonly message = signal<string | null>(null);
  readonly ok = signal(false);

  ngOnChanges(): void {
    this.load();
  }

  load(): void {
    this.ai.getSettings().subscribe({
      next: (s) => this.settings.set({ ...s }),
      error: (err) => this.fail(err, 'Failed to load AI defaults'),
    });
    this.ai.listUseCases().subscribe({
      next: (cases) => this.rows.set(cases.map((uc) => this.toRow(uc))),
      error: (err) => this.fail(err, 'Failed to load AI use cases'),
    });
  }

  providerName(provider: string): string {
    return this.providers.find((p) => p.provider === provider)?.display_name ?? provider;
  }

  rowProviders(row: UseCaseRow): string[] {
    const fromOptions = row.useCase.options.map((o) => o.provider);
    return [...new Set(row.provider ? [...fromOptions, row.provider] : fromOptions)];
  }

  rowModels(row: UseCaseRow): AiModelOption[] {
    return row.useCase.options.filter((o) => o.provider === row.provider);
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

  assign(row: UseCaseRow): void {
    const body: AiUseCaseModelUpdate = {
      provider: row.provider,
      model: row.custom ? row.customModel.trim() : row.model,
      custom: row.custom,
    };
    this.busy.set(true);
    this.ai.setUseCaseModel(row.useCase.use_case, body).subscribe({
      next: (updated) => {
        this.rows.update((rows) =>
          rows.map((r) => (r.useCase.use_case === updated.use_case ? this.toRow(updated) : r)),
        );
        this.busy.set(false);
        this.succeed(`${updated.display_name} now uses ${this.providerName(body.provider)} · ${body.model}`);
      },
      error: (err) => {
        this.busy.set(false);
        this.fail(err, 'Failed to assign model');
      },
    });
  }

  toggleHistory(row: UseCaseRow): void {
    if (row.history) {
      this.patchRow(row.useCase.use_case, { history: null });
      return;
    }
    this.ai.useCaseHistory(row.useCase.use_case).subscribe({
      next: (history) => this.patchRow(row.useCase.use_case, { history }),
      error: (err) => this.fail(err, 'Failed to load history'),
    });
  }

  private reloadUseCases(): void {
    this.ai.listUseCases().subscribe({ next: (cases) => this.rows.set(cases.map((uc) => this.toRow(uc))) });
  }

  private patchRow(useCase: string, patch: Partial<UseCaseRow>): void {
    this.rows.update((rows) => rows.map((r) => (r.useCase.use_case === useCase ? { ...r, ...patch } : r)));
  }

  private toRow(useCase: AiUseCase): UseCaseRow {
    const cur = useCase.current;
    const inOptions = !!cur && useCase.options.some((o) => o.provider === cur.provider && o.model === cur.model);
    const isCustom = !!cur?.updated_at && !inOptions;
    return {
      useCase,
      provider: cur?.provider ?? '',
      model: inOptions ? cur!.model : '',
      custom: isCustom,
      customModel: isCustom ? cur!.model : '',
      history: null,
    };
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
