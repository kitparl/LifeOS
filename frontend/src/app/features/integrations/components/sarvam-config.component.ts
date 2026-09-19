import { Component, Input, OnInit, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SecretInputComponent } from '../../../shared/secret-input/secret-input.component';
import {
  IntegrationsService,
  SarvamConfigStatus,
  SarvamConfigUpdate,
} from '../services/integrations.service';

@Component({
  selector: 'app-sarvam-config',
  standalone: true,
  imports: [FormsModule, SecretInputComponent],
  host: { class: 'contents' },
  template: `
    <div class="panel text-sm sm:col-span-2 lg:col-span-2">
      <div class="flex items-start justify-between gap-2">
        <div>
          <p class="font-medium">{{ displayName }}</p>
          <p class="text-gray-600 text-xs mt-1">{{ description }}</p>
        </div>
        @if (sarvam()) {
          <span
            class="text-xs shrink-0"
            [style.color]="sarvam()!.configured && sarvam()!.enabled ? 'var(--success)' : 'var(--text-muted)'"
          >
            {{ sarvamStatusLabel() }}
          </span>
        }
      </div>

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">How to connect</summary>
        <ol class="mt-2 list-decimal pl-4 space-y-1" style="color: var(--text-muted)">
          <li>
            Create an API key at
            <a href="https://dashboard.sarvam.ai/" target="_blank" rel="noopener noreferrer">dashboard.sarvam.ai</a>.
          </li>
          <li>Paste the key below (encrypted at rest; never shown raw after save).</li>
          <li>Save, then Test connection. Usage is billed to your Sarvam account (BYOK).</li>
          <li>Use <strong>AI Feedback</strong> in Communication → Writing.</li>
        </ol>
      </details>

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">Credentials &amp; configuration</summary>
        <div class="mt-3 flex flex-col gap-2 max-w-xl">
          <div class="flex flex-col gap-1">
            <label class="form-label" for="sarvam-key">API subscription key</label>
            <app-secret-input
              inputId="sarvam-key"
              [(ngModel)]="sarvamKeyInput"
              [placeholder]="sarvamKeyPlaceholder()"
              autocomplete="off"
            />
            @if (sarvam()?.configured && sarvam()?.api_key_masked) {
              <p class="text-xs" style="color: var(--text-muted)">
                Configured: {{ sarvam()!.api_key_masked }} (leave blank to keep)
              </p>
            }
          </div>
          <label class="flex items-center gap-2 text-xs mt-1">
            <input type="checkbox" [(ngModel)]="sarvamEnabled" />
            Enable Sarvam for writing feedback
          </label>
          <div class="flex flex-wrap gap-2 mt-2">
            <button type="button" class="btn-primary text-xs" [disabled]="svBusy()" (click)="saveSarvam()">
              {{ svBusy() ? 'Saving…' : 'Save' }}
            </button>
            <button
              type="button"
              class="btn-primary text-xs"
              [disabled]="svBusy() || !sarvam()?.configured"
              (click)="testSarvam()"
            >
              Test connection
            </button>
          </div>
          @if (svMessage()) {
            <p class="text-xs mt-1" [style.color]="svOk() ? 'var(--success)' : 'var(--danger)'">
              {{ svMessage() }}
            </p>
          }
          @if (sarvam()?.last_sync_at) {
            <p class="text-xs" style="color: var(--text-muted)">
              Last test: {{ sarvam()!.last_sync_at }}
            </p>
          }
        </div>
      </details>
    </div>
  `,
})
export class SarvamConfigComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);

  @Input({ required: true }) displayName = '';
  @Input({ required: true }) description = '';

  readonly connectionsChanged = output<void>();

  readonly sarvam = signal<SarvamConfigStatus | null>(null);
  readonly svBusy = signal(false);
  readonly svMessage = signal<string | null>(null);
  readonly svOk = signal(false);
  sarvamKeyInput = '';
  sarvamEnabled = false;

  ngOnInit(): void {
    this.loadSarvam();
  }

  applySarvamForm(status: SarvamConfigStatus): void {
    this.sarvam.set(status);
    this.sarvamEnabled = status.enabled;
    this.sarvamKeyInput = '';
  }

  loadSarvam(): void {
    this.integrations.getSarvam().subscribe({
      next: (status) => this.applySarvamForm(status),
      error: () => {
        this.svOk.set(false);
        this.svMessage.set('Failed to load Sarvam settings');
      },
    });
  }

  sarvamStatusLabel(): string {
    const s = this.sarvam();
    if (!s) return '';
    if (s.configured && s.enabled) return 'Connected';
    if (s.configured) return 'Configured (disabled)';
    return s.status || 'Not configured';
  }

  sarvamKeyPlaceholder(): string {
    const masked = this.sarvam()?.api_key_masked;
    return masked ? `Saved: ${masked}` : 'Paste Sarvam API key';
  }

  saveSarvam(): void {
    this.svBusy.set(true);
    this.svMessage.set(null);
    const body: SarvamConfigUpdate = { enabled: this.sarvamEnabled };
    if (this.sarvamKeyInput.trim()) {
      body.api_key = this.sarvamKeyInput.trim();
    }
    this.integrations.saveSarvamConfig(body).subscribe({
      next: (status) => {
        this.applySarvamForm(status);
        this.svOk.set(true);
        this.svMessage.set('Sarvam settings saved');
        this.svBusy.set(false);
        this.connectionsChanged.emit();
      },
      error: (err) => {
        this.svOk.set(false);
        this.svMessage.set(err?.error?.detail || 'Failed to save Sarvam settings');
        this.svBusy.set(false);
      },
    });
  }

  testSarvam(): void {
    this.svBusy.set(true);
    this.svMessage.set(null);
    this.integrations.testSarvam().subscribe({
      next: (res) => {
        this.svOk.set(res.ok);
        this.svMessage.set(res.detail);
        this.svBusy.set(false);
        if (res.ok) this.loadSarvam();
      },
      error: (err) => {
        this.svOk.set(false);
        this.svMessage.set(err?.error?.detail || 'Sarvam test failed');
        this.svBusy.set(false);
      },
    });
  }
}
