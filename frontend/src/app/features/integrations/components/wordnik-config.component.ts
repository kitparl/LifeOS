import { Component, Input, OnInit, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { SecretInputComponent } from '../../../shared/secret-input/secret-input.component';
import { WordOfTheDayService } from '../../communication/vocabulary/services/word-of-the-day.service';
import { IntegrationsService, WordnikConfigStatus } from '../services/integrations.service';
import { apiErrorMessage } from '../../../core/utils/http';

@Component({
  selector: 'app-wordnik-config',
  standalone: true,
  imports: [FormsModule, SecretInputComponent],
  host: { class: 'contents' },
  template: `
    <div id="wordnik" class="panel text-sm">
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
          <li>Sign up at <strong>developer.wordnik.com</strong> and copy your API key (free tier: 100 calls/hour).</li>
          <li>Paste it below, Save, then Test connection.</li>
          <li>Use it in Communication → Vocabulary → Word Lab and the Word of the Day in the header.</li>
          <li>Details: <code>setup/WORDNIK_SETUP.md</code>.</li>
        </ol>
      </details>

      <details class="mt-3 text-xs" [open]="!config()?.configured">
        <summary class="cursor-pointer font-medium">API key</summary>
        <div class="mt-3 flex flex-col gap-2">
          <div class="flex flex-col gap-1">
            <label class="form-label" for="wordnik-key">Wordnik API key</label>
            <app-secret-input inputId="wordnik-key" [(ngModel)]="keyInput" [placeholder]="keyPlaceholder()" autocomplete="off" />
            @if (config()?.api_key_masked) {
              <p class="text-xs" style="color: var(--text-muted)">Configured: {{ config()!.api_key_masked }} (leave blank to keep)</p>
            }
          </div>
          @if (config()?.configured) {
            <label class="flex items-center gap-2 text-xs">
              <input type="checkbox" [(ngModel)]="enabled" />
              Enable Wordnik
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
          @if (config()?.last_tested_at) {
            <p class="text-xs" style="color: var(--text-muted)">Last test: {{ config()!.last_tested_at }}</p>
          }
        </div>
      </details>
    </div>
  `,
})
export class WordnikConfigComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);
  private readonly auth = inject(AuthService);
  private readonly wordOfTheDay = inject(WordOfTheDayService);

  @Input({ required: true }) displayName = '';
  @Input({ required: true }) description = '';

  readonly connectionsChanged = output<void>();

  readonly config = signal<WordnikConfigStatus | null>(null);
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

  keyPlaceholder(): string {
    const masked = this.config()?.api_key_masked;
    return masked ? `Saved: ${masked}` : 'Paste Wordnik API key';
  }

  private apply(status: WordnikConfigStatus): void {
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
    this.integrations.getWordnik().subscribe({
      next: (status) => this.apply(status),
      error: (err) => this.fail(err, 'Failed to load Wordnik settings'),
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
    const body = key ? { api_key: key } : { enabled: this.enabled };
    this.integrations.saveWordnikConfig(body).subscribe({
      next: (status) => {
        this.apply(status);
        this.ok.set(true);
        this.message.set('Wordnik settings saved');
        this.busy.set(false);
        this.connectionsChanged.emit();
      },
      error: (err) => this.fail(err, 'Failed to save Wordnik settings'),
    });
  }

  test(): void {
    this.busy.set(true);
    this.message.set(null);
    this.integrations.testWordnik().subscribe({
      next: (res) => {
        this.ok.set(res.ok);
        this.message.set(res.detail);
        this.busy.set(false);
        this.load();
      },
      error: (err) => this.fail(err, 'Wordnik test failed'),
    });
  }

  remove(): void {
    const id = this.config()?.connection_id;
    if (!id) return;
    this.busy.set(true);
    this.integrations.remove(id).subscribe({
      next: () => {
        const userId = this.auth.user()?.id;
        if (userId) this.wordOfTheDay.clearCache(userId);
        this.ok.set(true);
        this.message.set('Wordnik key removed');
        this.busy.set(false);
        this.connectionsChanged.emit();
        this.load();
      },
      error: (err) => this.fail(err, 'Failed to remove Wordnik key'),
    });
  }
}
