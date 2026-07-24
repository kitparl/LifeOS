import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  IntegrationConnection,
  IntegrationProvider,
  IntegrationsService,
  TelegramConfigStatus,
} from './services/integrations.service';

@Component({
  selector: 'app-integrations-page',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">Integration Hub</h1>
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        @for (p of providers; track p.provider) {
          @if (p.provider === 'telegram') {
            <div class="panel text-sm sm:col-span-2 lg:col-span-2">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <p class="font-medium">{{ p.display_name }}</p>
                  <p class="text-gray-600 text-xs mt-1">{{ p.description }}</p>
                </div>
                @if (telegram()) {
                  <span
                    class="text-xs shrink-0"
                    [style.color]="telegram()!.configured && telegram()!.enabled ? 'var(--success)' : 'var(--text-muted)'"
                  >
                    {{ telegramStatusLabel() }}
                  </span>
                }
              </div>

              <details class="mt-3 text-xs">
                <summary class="cursor-pointer font-medium">How to integrate your bot</summary>
                <ol class="mt-2 list-decimal pl-4 space-y-1" style="color: var(--text-muted)">
                  <li>Open Telegram, search <strong>&#64;BotFather</strong>, send <code>/newbot</code>, follow the prompts, and copy the HTTP API token.</li>
                  <li>Paste the token into the <strong>Bot Token</strong> field below (it is stored encrypted and never shown again in full).</li>
                  <li>Start a chat with your new bot (press <strong>Start</strong>) or add it to the group/channel you want notifications in.</li>
                  <li>
                    Get your chat id: send any message to the bot, then click <strong>Detect chat id</strong>.
                    Fallback: message <strong>&#64;userinfobot</strong> and copy your Id.
                  </li>
                  <li>Click <strong>Send test message</strong> to verify the connection.</li>
                </ol>
              </details>

              <div class="mt-3 flex flex-col gap-2 max-w-md">
                <div class="flex flex-col gap-1">
                  <label class="form-label" for="tg-token">Bot Token</label>
                  <input
                    id="tg-token"
                    class="input-field"
                    type="password"
                    autocomplete="off"
                    [(ngModel)]="botTokenInput"
                    [placeholder]="tokenPlaceholder()"
                  />
                  @if (telegram()?.configured && telegram()?.bot_token_masked) {
                    <p class="text-xs" style="color: var(--text-muted)">
                      Configured: {{ telegram()!.bot_token_masked }} (leave blank to keep)
                    </p>
                  }
                </div>
                <div class="flex flex-col gap-1">
                  <label class="form-label" for="tg-chat">Chat ID</label>
                  <div class="flex gap-2">
                    <input
                      id="tg-chat"
                      class="input-field flex-1"
                      type="text"
                      [(ngModel)]="chatIdInput"
                      placeholder="e.g. 123456789"
                    />
                    <button
                      type="button"
                      class="btn-primary text-xs shrink-0"
                      [disabled]="tgBusy()"
                      (click)="detectChatId()"
                    >
                      Detect chat id
                    </button>
                  </div>
                </div>
                <label class="flex items-center gap-2 text-xs mt-1">
                  <input type="checkbox" [(ngModel)]="telegramEnabled" />
                  Enable Telegram notifications
                </label>
                <div class="flex flex-wrap gap-2 mt-1">
                  <button
                    type="button"
                    class="btn-primary text-xs"
                    [disabled]="tgBusy()"
                    (click)="saveTelegram()"
                  >
                    {{ tgBusy() ? 'Saving…' : 'Save' }}
                  </button>
                  <button
                    type="button"
                    class="btn-primary text-xs"
                    [disabled]="tgBusy() || !telegram()?.configured"
                    (click)="testTelegram()"
                  >
                    Send test message
                  </button>
                  <button
                    type="button"
                    class="text-xs"
                    [disabled]="tgBusy() || !telegram()?.configured"
                    (click)="sendDigest()"
                  >
                    Send digest
                  </button>
                </div>
                @if (tgMessage()) {
                  <p
                    class="text-xs mt-1"
                    [style.color]="tgOk() ? 'var(--success)' : 'var(--danger)'"
                  >
                    {{ tgMessage() }}
                  </p>
                }
                @if (telegram()?.last_sync_at) {
                  <p class="text-xs" style="color: var(--text-muted)">
                    Last test/sync: {{ telegram()!.last_sync_at }}
                  </p>
                }
              </div>
            </div>
          } @else {
            <div class="panel text-sm">
              <p class="font-medium">{{ p.display_name }}</p>
              <p class="text-gray-600 text-xs mt-1">{{ p.description }}</p>
              @if (isConnected(p.provider)) {
                <p class="text-xs text-green-700 mt-2">Connected</p>
                <div class="flex gap-2 mt-2">
                  <button type="button" class="btn-primary text-xs" (click)="sync(p.provider)">Sync</button>
                  <button type="button" class="text-xs" style="color: var(--danger)" (click)="disconnect(p.provider)">Remove</button>
                </div>
              } @else {
                <button type="button" class="btn-primary text-xs mt-2" (click)="connect(p.provider)">Connect</button>
              }
            </div>
          }
        }
      </div>
      @if (lastSyncMsg) {
        <p class="text-sm" style="color: var(--text-muted)">{{ lastSyncMsg }}</p>
      }
    </div>
  `,
})
export class IntegrationsPageComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);
  providers: IntegrationProvider[] = [];
  connections: IntegrationConnection[] = [];
  lastSyncMsg: string | null = null;

  readonly telegram = signal<TelegramConfigStatus | null>(null);
  readonly tgBusy = signal(false);
  readonly tgMessage = signal<string | null>(null);
  readonly tgOk = signal(false);

  botTokenInput = '';
  chatIdInput = '';
  telegramEnabled = false;

  ngOnInit(): void {
    this.integrations.providers().subscribe({ next: (p) => (this.providers = p) });
    this.loadConnections();
    this.loadTelegram();
  }

  loadConnections(): void {
    this.integrations.list().subscribe({ next: (c) => (this.connections = c) });
  }

  loadTelegram(): void {
    this.integrations.getTelegram().subscribe({
      next: (status) => {
        this.telegram.set(status);
        this.chatIdInput = status.chat_id ?? '';
        this.telegramEnabled = status.enabled;
        this.botTokenInput = '';
      },
      error: () => {
        this.tgOk.set(false);
        this.tgMessage.set('Failed to load Telegram settings');
      },
    });
  }

  telegramStatusLabel(): string {
    const t = this.telegram();
    if (!t) return '';
    if (t.configured && t.enabled) return 'Connected';
    if (t.configured) return 'Configured (disabled)';
    return t.status || 'Not configured';
  }

  tokenPlaceholder(): string {
    const masked = this.telegram()?.bot_token_masked;
    return masked ? `Saved: ${masked}` : 'Paste bot token from @BotFather';
  }

  isConnected(provider: string): boolean {
    return this.connections.some((c) => c.provider === provider && c.enabled);
  }

  connId(provider: string): string | undefined {
    return this.connections.find((c) => c.provider === provider)?.id;
  }

  connect(provider: string): void {
    this.integrations.connect(provider).subscribe({ next: () => this.loadConnections() });
  }

  disconnect(provider: string): void {
    const id = this.connId(provider);
    if (!id) return;
    this.integrations.remove(id).subscribe({ next: () => this.loadConnections() });
  }

  sync(provider: string): void {
    const id = this.connId(provider);
    if (!id) return;
    this.integrations.sync(id).subscribe({
      next: (r) => {
        this.lastSyncMsg = r.message;
        this.loadConnections();
      },
    });
  }

  saveTelegram(): void {
    this.tgBusy.set(true);
    this.tgMessage.set(null);
    const body: { bot_token?: string; chat_id?: string; enabled: boolean } = {
      enabled: this.telegramEnabled,
    };
    if (this.botTokenInput.trim()) {
      body.bot_token = this.botTokenInput.trim();
    }
    if (this.chatIdInput.trim()) {
      body.chat_id = this.chatIdInput.trim();
    }
    this.integrations.saveTelegramConfig(body).subscribe({
      next: (status) => {
        this.telegram.set(status);
        this.botTokenInput = '';
        this.chatIdInput = status.chat_id ?? this.chatIdInput;
        this.telegramEnabled = status.enabled;
        this.tgOk.set(true);
        this.tgMessage.set('Telegram settings saved');
        this.tgBusy.set(false);
        this.loadConnections();
      },
      error: (err) => {
        this.tgOk.set(false);
        this.tgMessage.set(err?.error?.detail ?? 'Failed to save Telegram settings');
        this.tgBusy.set(false);
      },
    });
  }

  testTelegram(): void {
    const id = this.telegram()?.connection_id;
    if (!id) return;
    this.tgBusy.set(true);
    this.tgMessage.set(null);
    this.integrations.testConnection(id).subscribe({
      next: (r) => {
        this.tgOk.set(r.ok);
        this.tgMessage.set(
          r.ok
            ? `Test OK${r.bot_username ? ` (@${r.bot_username})` : ''}: ${r.detail}`
            : r.detail,
        );
        this.tgBusy.set(false);
        this.loadTelegram();
      },
      error: (err) => {
        this.tgOk.set(false);
        this.tgMessage.set(err?.error?.detail ?? 'Test failed');
        this.tgBusy.set(false);
      },
    });
  }

  detectChatId(): void {
    const id = this.telegram()?.connection_id;
    if (!id) return;
    this.tgBusy.set(true);
    this.tgMessage.set(null);
    const body = this.botTokenInput.trim() ? { bot_token: this.botTokenInput.trim() } : undefined;
    this.integrations.detectChatId(id, body).subscribe({
      next: (r) => {
        if (r.candidates.length > 0) {
          this.chatIdInput = r.candidates[0].chat_id;
          this.tgOk.set(true);
          const labels = r.candidates
            .map((c) => `${c.chat_id}${c.title ? ` (${c.title})` : ''}`)
            .join(', ');
          this.tgMessage.set(`${r.detail} Filled first: ${labels}`);
        } else {
          this.tgOk.set(false);
          this.tgMessage.set(r.detail);
        }
        this.tgBusy.set(false);
      },
      error: (err) => {
        this.tgOk.set(false);
        this.tgMessage.set(err?.error?.detail ?? 'Detect chat id failed');
        this.tgBusy.set(false);
      },
    });
  }

  sendDigest(): void {
    this.tgBusy.set(true);
    this.tgMessage.set(null);
    this.integrations.sendDigest().subscribe({
      next: (r) => {
        this.tgOk.set(r.sent);
        const parts = Object.entries(r.sections || {})
          .map(([k, v]) => `${k}:${v}`)
          .join(', ');
        this.tgMessage.set(`${r.detail}${parts ? ` (${parts})` : ''}`);
        this.tgBusy.set(false);
        this.loadTelegram();
      },
      error: (err) => {
        this.tgOk.set(false);
        this.tgMessage.set(err?.error?.detail ?? 'Digest failed');
        this.tgBusy.set(false);
      },
    });
  }
}
