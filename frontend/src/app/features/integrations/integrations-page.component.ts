import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SecretInputComponent } from '../../shared/secret-input/secret-input.component';
import {
  GitHubConfigStatus,
  GitHubConfigUpdate,
  IntegrationConnection,
  IntegrationProvider,
  IntegrationsService,
  ReportJobType,
  ReportRun,
  TELEGRAM_EVENT_OPTIONS,
  TelegramConfigStatus,
  TelegramConfigUpdate,
  TelegramWebhookStatus,
} from './services/integrations.service';

@Component({
  selector: 'app-integrations-page',
  standalone: true,
  imports: [FormsModule, SecretInputComponent],
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
                  <li>Optionally register a <strong>webhook</strong> (requires PUBLIC_BASE_URL HTTPS) for two-way commands like /tasks.</li>
                </ol>
              </details>

              <details class="mt-3 text-xs">
                <summary class="cursor-pointer font-medium">Credentials &amp; configuration</summary>
              <div class="mt-3 flex flex-col gap-2 max-w-xl">
                <div class="flex flex-col gap-1">
                  <label class="form-label" for="tg-token">Bot Token</label>
                  <app-secret-input
                    inputId="tg-token"
                    [(ngModel)]="botTokenInput"
                    [placeholder]="tokenPlaceholder()"
                    autocomplete="off"
                  />
                  @if (telegram()?.configured && telegram()?.bot_token_masked) {
                    <p class="text-xs" style="color: var(--text-muted)">
                      Configured: {{ telegram()!.bot_token_masked }} (leave blank to keep)
                    </p>
                  }
                </div>
                <div class="flex flex-col gap-1">
                  <label class="form-label" for="tg-chat">Chat ID</label>
                  <div class="flex gap-2 items-stretch">
                    <div class="flex-1 min-w-0">
                      <app-secret-input
                        inputId="tg-chat"
                        [(ngModel)]="chatIdInput"
                        placeholder="e.g. 123456789"
                      />
                    </div>
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

                <div class="mt-3 border-t pt-3" style="border-color: var(--border)">
                  <p class="font-medium text-xs mb-2">Notify on events</p>
                  <div class="grid grid-cols-2 gap-1">
                    @for (opt of eventOptions; track opt.key) {
                      <label class="flex items-center gap-2 text-xs">
                        <input
                          type="checkbox"
                          [checked]="notifyOn.has(opt.key)"
                          (change)="toggleNotify(opt.key, $event)"
                        />
                        {{ opt.label }}
                      </label>
                    }
                  </div>
                </div>

                <div class="mt-3 border-t pt-3" style="border-color: var(--border)">
                  <p class="font-medium text-xs mb-2">Scheduled reports</p>
                  <p class="text-xs mb-2" style="color: var(--text-muted)">
                    Defaults use Asia/Kolkata (IST). Morning replaces the old digest.
                  </p>
                  <div class="grid gap-2 sm:grid-cols-2">
                    <label class="flex items-center gap-2 text-xs">
                      <input type="checkbox" [(ngModel)]="morningEnabled" />
                      Morning
                    </label>
                    <div>
                      <input class="input-field w-full" type="time" [(ngModel)]="morningTime" />
                      <p class="text-xs mt-1" style="color: var(--text-muted)">
                        {{ nextRunLabel('morning') }}
                      </p>
                    </div>
                    <label class="flex items-center gap-2 text-xs">
                      <input type="checkbox" [(ngModel)]="middayEnabled" />
                      Midday nudge
                    </label>
                    <div>
                      <input class="input-field w-full" type="time" [(ngModel)]="middayTime" />
                      <p class="text-xs mt-1" style="color: var(--text-muted)">
                        {{ nextRunLabel('midday') }}
                      </p>
                    </div>
                    <label class="flex items-center gap-2 text-xs">
                      <input type="checkbox" [(ngModel)]="nightEnabled" />
                      Night wrap
                    </label>
                    <div>
                      <input class="input-field w-full" type="time" [(ngModel)]="nightTime" />
                      <p class="text-xs mt-1" style="color: var(--text-muted)">
                        {{ nextRunLabel('night') }}
                      </p>
                    </div>
                    <label class="flex items-center gap-2 text-xs">
                      <input type="checkbox" [(ngModel)]="weeklyEnabled" />
                      Weekly review
                    </label>
                    <div>
                      <div class="flex gap-1">
                        <input class="input-field flex-1" type="time" [(ngModel)]="weeklyTime" />
                        <select class="input-field" [(ngModel)]="weeklyWeekday">
                          <option [ngValue]="0">Mon</option>
                          <option [ngValue]="1">Tue</option>
                          <option [ngValue]="2">Wed</option>
                          <option [ngValue]="3">Thu</option>
                          <option [ngValue]="4">Fri</option>
                          <option [ngValue]="5">Sat</option>
                          <option [ngValue]="6">Sun</option>
                        </select>
                      </div>
                      <p class="text-xs mt-1" style="color: var(--text-muted)">
                        {{ nextRunLabel('weekly') }}
                      </p>
                    </div>
                    <label class="flex items-center gap-2 text-xs">
                      <input type="checkbox" [(ngModel)]="aiBriefingEnabled" />
                      AI briefing
                    </label>
                    <div>
                      <input class="input-field w-full" type="time" [(ngModel)]="aiBriefingTime" />
                      <p class="text-xs mt-1" style="color: var(--text-muted)">
                        {{ nextRunLabel('ai_briefing') }}
                      </p>
                    </div>
                    <div class="flex flex-col gap-1 sm:col-span-2">
                      <label class="form-label" for="tg-tz">Timezone</label>
                      <input
                        id="tg-tz"
                        class="input-field"
                        type="text"
                        [(ngModel)]="timezone"
                        placeholder="Asia/Kolkata"
                      />
                      @if (timezone !== detectedTimezone) {
                        <p class="text-xs" style="color: var(--warning)">
                          Reports fire in {{ timezone }}, but this device is in
                          {{ detectedTimezone }}.
                          <button type="button" class="underline" (click)="useDetectedTimezone()">
                            Use {{ detectedTimezone }}
                          </button>
                        </p>
                      }
                    </div>
                  </div>
                  @if (telegram()?.scheduler_warning) {
                    <p class="text-xs mt-2" style="color: var(--danger)">
                      {{ telegram()!.scheduler_warning }}
                    </p>
                  }
                  <p class="font-medium text-xs mt-3 mb-1">Reminders</p>
                  <div class="flex flex-wrap gap-3 text-xs">
                    <label class="flex items-center gap-2">
                      <input type="checkbox" [(ngModel)]="birthdayReminders" />
                      Birthdays
                    </label>
                    <label class="flex items-center gap-2">
                      <input type="checkbox" [(ngModel)]="immutableReminders" />
                      Immutable events
                    </label>
                    <label class="flex items-center gap-2">
                      <input type="checkbox" [(ngModel)]="routineReminders" />
                      Routine blocks
                    </label>
                  </div>
                  <div class="flex flex-wrap gap-2 mt-3">
                    @for (jt of reportJobTypes; track jt) {
                      <button
                        type="button"
                        class="text-xs btn-secondary"
                        [disabled]="tgBusy() || !telegram()?.configured"
                        (click)="runReportNow(jt)"
                      >
                        Send {{ jt }} now
                      </button>
                    }
                    <button type="button" class="text-xs" [disabled]="tgBusy()" (click)="loadReportRuns()">
                      Refresh runs
                    </button>
                  </div>
                  @if (reportRuns().length) {
                    <ul class="mt-2 text-xs space-y-1" style="color: var(--text-muted)">
                      @for (r of reportRuns(); track r.id) {
                        <li>
                          {{ r.job_type }} · {{ r.status }}
                          @if (r.skip_reason) { ({{ r.skip_reason }}) }
                          · {{ r.created_at }}
                        </li>
                      }
                    </ul>
                  }
                  @if (telegram()?.last_digest_at) {
                    <p class="text-xs mt-1" style="color: var(--text-muted)">
                      Last morning: {{ telegram()!.last_digest_at }}
                    </p>
                  }
                </div>

                <div class="mt-3 border-t pt-3" style="border-color: var(--border)">
                  <p class="font-medium text-xs mb-2">Two-way webhook</p>
                  <p class="text-xs mb-2" style="color: var(--text-muted)">
                    @if (webhook()?.url || telegram()?.webhook_url) {
                      Active: {{ webhook()?.url || telegram()?.webhook_url }}
                    } @else if (telegram()?.webhook_configured) {
                      Secret stored — register to push URL to Telegram.
                    } @else {
                      Not registered. Requires PUBLIC_BASE_URL (HTTPS) on the server.
                    }
                  </p>
                  @if (webhook()?.last_error_message) {
                    <p class="text-xs mb-2" style="color: var(--danger)">
                      {{ webhook()!.last_error_message }}
                    </p>
                  }
                  <div class="flex flex-wrap gap-2">
                    <button
                      type="button"
                      class="btn-primary text-xs"
                      [disabled]="tgBusy() || !telegram()?.configured"
                      (click)="registerWebhook()"
                    >
                      Register webhook
                    </button>
                    <button
                      type="button"
                      class="text-xs"
                      [disabled]="tgBusy()"
                      (click)="deleteWebhook()"
                    >
                      Disable webhook
                    </button>
                    <button
                      type="button"
                      class="text-xs"
                      [disabled]="tgBusy()"
                      (click)="refreshWebhook()"
                    >
                      Refresh status
                    </button>
                  </div>
                </div>

                <div class="flex flex-wrap gap-2 mt-3">
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
                    Send digest now
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
              </details>
            </div>
          } @else if (p.provider === 'github') {
            <div class="panel text-sm sm:col-span-2 lg:col-span-2">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <p class="font-medium">{{ p.display_name }}</p>
                  <p class="text-gray-600 text-xs mt-1">{{ p.description }}</p>
                </div>
                @if (github()) {
                  <span
                    class="text-xs shrink-0"
                    [style.color]="github()!.configured && github()!.enabled ? 'var(--success)' : 'var(--text-muted)'"
                  >
                    {{ githubStatusLabel() }}
                  </span>
                }
              </div>

              <details class="mt-3 text-xs">
                <summary class="cursor-pointer font-medium">How to connect</summary>
                <ol class="mt-2 list-decimal pl-4 space-y-1" style="color: var(--text-muted)">
                  <li>Create a fine-grained PAT with <strong>Contents: Read and write</strong> on your notes repo.</li>
                  <li>Paste the token below (encrypted at rest; use the eye to reveal when editing).</li>
                  <li>Set repository as <code>owner/repo</code>, then Save and Test connection.</li>
                  <li>In Knowledge Notes, use the ↗ button on a section to push markdown and images.</li>
                </ol>
              </details>

              <details class="mt-3 text-xs" open>
                <summary class="cursor-pointer font-medium">Credentials &amp; configuration</summary>
                <div class="mt-3 flex flex-col gap-2 max-w-xl">
                  <div class="flex flex-col gap-1">
                    <label class="form-label" for="gh-token">Personal Access Token</label>
                    <app-secret-input
                      inputId="gh-token"
                      [(ngModel)]="githubTokenInput"
                      [placeholder]="githubTokenPlaceholder()"
                      autocomplete="off"
                    />
                    @if (github()?.configured && github()?.token_masked) {
                      <p class="text-xs" style="color: var(--text-muted)">
                        Configured: {{ github()!.token_masked }} (leave blank to keep)
                      </p>
                    }
                  </div>
                  <div class="flex flex-col gap-1">
                    <label class="form-label" for="gh-repo">Repository</label>
                    <input
                      id="gh-repo"
                      class="input-field"
                      [(ngModel)]="githubRepoInput"
                      placeholder="your-user/lifeos-notes"
                    />
                  </div>
                  <div class="flex flex-col gap-1">
                    <label class="form-label" for="gh-branch">Branch</label>
                    <input id="gh-branch" class="input-field" [(ngModel)]="githubBranchInput" placeholder="main" />
                  </div>
                  <div class="flex flex-col gap-1">
                    <label class="form-label" for="gh-base">Base path</label>
                    <input
                      id="gh-base"
                      class="input-field"
                      [(ngModel)]="githubBasePathInput"
                      placeholder="(empty = repo root)"
                    />
                    <p class="text-xs" style="color: var(--text-muted)">
                      Leave blank to sync as <code>python/</code>, <code>system-design/</code> at the repo root.
                    </p>
                  </div>
                  <label class="flex items-center gap-2 text-xs mt-1">
                    <input type="checkbox" [(ngModel)]="githubEnabled" />
                    Enable GitHub sync
                  </label>
                  <label class="flex items-center gap-2 text-xs">
                    <input type="checkbox" [(ngModel)]="githubNotifyInApp" />
                    Notify in-app on GitHub sync
                  </label>
                  <label class="flex items-center gap-2 text-xs">
                    <input type="checkbox" [(ngModel)]="githubNotifyTelegram" />
                    Notify via Telegram on GitHub sync
                  </label>
                  <p class="text-xs" style="color: var(--text-muted)">
                    Telegram delivery also requires Telegram to be configured and enabled.
                  </p>
                  <div class="flex flex-wrap gap-2 mt-2">
                    <button type="button" class="btn-primary text-xs" [disabled]="ghBusy()" (click)="saveGitHub()">
                      {{ ghBusy() ? 'Saving…' : 'Save' }}
                    </button>
                    <button
                      type="button"
                      class="btn-primary text-xs"
                      [disabled]="ghBusy() || !github()?.configured"
                      (click)="testGitHub()"
                    >
                      Test connection
                    </button>
                  </div>
                  @if (ghMessage()) {
                    <p class="text-xs mt-1" [style.color]="ghOk() ? 'var(--success)' : 'var(--danger)'">
                      {{ ghMessage() }}
                    </p>
                  }
                  @if (github()?.last_sync_at) {
                    <p class="text-xs" style="color: var(--text-muted)">
                      Last test/sync: {{ github()!.last_sync_at }}
                    </p>
                  }
                </div>
              </details>
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
  readonly eventOptions = TELEGRAM_EVENT_OPTIONS;

  readonly telegram = signal<TelegramConfigStatus | null>(null);
  readonly webhook = signal<TelegramWebhookStatus | null>(null);
  readonly tgBusy = signal(false);
  readonly tgMessage = signal<string | null>(null);
  readonly tgOk = signal(false);

  readonly github = signal<GitHubConfigStatus | null>(null);
  readonly ghBusy = signal(false);
  readonly ghMessage = signal<string | null>(null);
  readonly ghOk = signal(false);
  githubTokenInput = '';
  githubRepoInput = '';
  githubBranchInput = 'main';
  githubBasePathInput = '';
  githubEnabled = false;
  githubNotifyInApp = false;
  githubNotifyTelegram = false;

  botTokenInput = '';
  chatIdInput = '';
  telegramEnabled = false;
  notifyOn = new Set<string>(TELEGRAM_EVENT_OPTIONS.map((o) => o.key));
  morningEnabled = true;
  morningTime = '06:00';
  middayEnabled = true;
  middayTime = '12:30';
  nightEnabled = true;
  nightTime = '22:00';
  weeklyEnabled = true;
  weeklyTime = '18:00';
  weeklyWeekday = 6;
  aiBriefingEnabled = false;
  aiBriefingTime = '08:00';
  birthdayReminders = true;
  immutableReminders = true;
  routineReminders = true;
  readonly detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata';
  timezone = this.detectedTimezone;
  readonly reportJobTypes: ReportJobType[] = ['morning', 'midday', 'night', 'weekly', 'ai_briefing'];
  readonly reportRuns = signal<ReportRun[]>([]);

  ngOnInit(): void {
    this.integrations.providers().subscribe({ next: (p) => (this.providers = p) });
    this.loadConnections();
    this.loadTelegram();
    this.loadGitHub();
  }

  loadConnections(): void {
    this.integrations.list().subscribe({ next: (c) => (this.connections = c) });
  }

  applyTelegramForm(status: TelegramConfigStatus): void {
    this.telegram.set(status);
    this.chatIdInput = status.chat_id ?? '';
    this.telegramEnabled = status.enabled;
    this.botTokenInput = '';
    this.notifyOn = new Set(status.notify_on?.length ? status.notify_on : TELEGRAM_EVENT_OPTIONS.map((o) => o.key));
    this.morningEnabled = status.morning_enabled ?? status.digest_enabled ?? true;
    this.morningTime = status.morning_time || status.digest_time || '06:00';
    this.middayEnabled = status.midday_enabled ?? true;
    this.middayTime = status.midday_time || '12:30';
    this.nightEnabled = status.night_enabled ?? true;
    this.nightTime = status.night_time || '22:00';
    this.weeklyEnabled = status.weekly_enabled ?? true;
    this.weeklyTime = status.weekly_time || '18:00';
    this.weeklyWeekday = status.weekly_weekday ?? 6;
    this.aiBriefingEnabled = status.ai_briefing_enabled ?? false;
    this.aiBriefingTime = status.ai_briefing_time || '08:00';
    this.birthdayReminders = status.birthday_reminders_enabled ?? true;
    this.immutableReminders = status.immutable_reminders_enabled ?? true;
    this.routineReminders = status.routine_reminders_enabled ?? true;
    this.timezone = status.timezone || this.detectedTimezone;
  }

  useDetectedTimezone(): void {
    this.timezone = this.detectedTimezone;
  }

  nextRunLabel(jobType: ReportJobType): string {
    const raw = this.telegram()?.next_runs?.[jobType];
    if (!raw) return 'Not scheduled';
    const at = new Date(raw);
    if (Number.isNaN(at.getTime())) return 'Not scheduled';
    const when = at.toLocaleString(undefined, {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
    return `Next: ${when}`;
  }

  loadTelegram(): void {
    this.integrations.getTelegram().subscribe({
      next: (status) => {
        this.applyTelegramForm(status);
        this.refreshWebhook();
      },
      error: () => {
        this.tgOk.set(false);
        this.tgMessage.set('Failed to load Telegram settings');
      },
    });
  }

  applyGitHubForm(status: GitHubConfigStatus): void {
    this.github.set(status);
    this.githubRepoInput = status.repo ?? '';
    this.githubBranchInput = status.branch || 'main';
    this.githubBasePathInput = status.base_path ?? '';
    this.githubEnabled = status.enabled;
    this.githubNotifyInApp = status.notify_github_sync_in_app ?? false;
    this.githubNotifyTelegram = status.notify_github_sync_telegram ?? false;
    this.githubTokenInput = '';
  }

  loadGitHub(): void {
    this.integrations.getGitHub().subscribe({
      next: (status) => this.applyGitHubForm(status),
      error: () => {
        this.ghOk.set(false);
        this.ghMessage.set('Failed to load GitHub settings');
      },
    });
  }

  githubStatusLabel(): string {
    const g = this.github();
    if (!g) return '';
    if (g.configured && g.enabled) return 'Connected';
    if (g.configured) return 'Configured (disabled)';
    return g.status || 'Not configured';
  }

  githubTokenPlaceholder(): string {
    const masked = this.github()?.token_masked;
    return masked ? `Saved: ${masked}` : 'Paste GitHub PAT';
  }

  saveGitHub(): void {
    this.ghBusy.set(true);
    this.ghMessage.set(null);
    const body: GitHubConfigUpdate = {
      enabled: this.githubEnabled,
      repo: this.githubRepoInput.trim() || null,
      branch: this.githubBranchInput.trim() || null,
      base_path: this.githubBasePathInput.trim(),
      notify_github_sync_in_app: this.githubNotifyInApp,
      notify_github_sync_telegram: this.githubNotifyTelegram,
    };
    if (this.githubTokenInput.trim()) {
      body.token = this.githubTokenInput.trim();
    }
    this.integrations.saveGitHubConfig(body).subscribe({
      next: (status) => {
        this.applyGitHubForm(status);
        this.ghOk.set(true);
        this.ghMessage.set('GitHub settings saved');
        this.ghBusy.set(false);
        this.loadConnections();
      },
      error: (err) => {
        this.ghOk.set(false);
        this.ghMessage.set(err?.error?.detail || 'Failed to save GitHub settings');
        this.ghBusy.set(false);
      },
    });
  }

  testGitHub(): void {
    this.ghBusy.set(true);
    this.ghMessage.set(null);
    this.integrations.testGitHub().subscribe({
      next: (res) => {
        this.ghOk.set(res.ok);
        this.ghMessage.set(res.detail);
        this.ghBusy.set(false);
        if (res.ok) this.loadGitHub();
      },
      error: (err) => {
        this.ghOk.set(false);
        this.ghMessage.set(err?.error?.detail || 'GitHub test failed');
        this.ghBusy.set(false);
      },
    });
  }

  toggleNotify(key: string, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked) this.notifyOn.add(key);
    else this.notifyOn.delete(key);
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
    const body: TelegramConfigUpdate = {
      enabled: this.telegramEnabled,
      notify_on: Array.from(this.notifyOn),
      morning_enabled: this.morningEnabled,
      morning_time: this.morningTime,
      midday_enabled: this.middayEnabled,
      midday_time: this.middayTime,
      night_enabled: this.nightEnabled,
      night_time: this.nightTime,
      weekly_enabled: this.weeklyEnabled,
      weekly_time: this.weeklyTime,
      weekly_weekday: this.weeklyWeekday,
      ai_briefing_enabled: this.aiBriefingEnabled,
      ai_briefing_time: this.aiBriefingTime,
      birthday_reminders_enabled: this.birthdayReminders,
      immutable_reminders_enabled: this.immutableReminders,
      routine_reminders_enabled: this.routineReminders,
      timezone: this.timezone.trim() || this.detectedTimezone,
      // Keep digest_* in sync for legacy
      digest_enabled: this.morningEnabled,
      digest_time: this.morningTime,
    };
    if (this.botTokenInput.trim()) {
      body.bot_token = this.botTokenInput.trim();
    }
    if (this.chatIdInput.trim()) {
      body.chat_id = this.chatIdInput.trim();
    }
    this.integrations.saveTelegramConfig(body).subscribe({
      next: (status) => {
        this.applyTelegramForm(status);
        this.tgOk.set(!status.scheduler_warning);
        this.tgMessage.set(status.scheduler_warning || 'Telegram settings saved');
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

  runReportNow(jobType: ReportJobType): void {
    this.tgBusy.set(true);
    this.tgMessage.set(null);
    this.integrations.runReport(jobType).subscribe({
      next: (r) => {
        this.tgOk.set(r.sent);
        this.tgMessage.set(`${jobType}: ${r.detail}`);
        this.tgBusy.set(false);
        this.loadReportRuns();
      },
      error: (err) => {
        this.tgOk.set(false);
        this.tgMessage.set(err?.error?.detail ?? `Failed to run ${jobType}`);
        this.tgBusy.set(false);
      },
    });
  }

  loadReportRuns(): void {
    this.integrations.listReportRuns(15).subscribe({
      next: (runs) => this.reportRuns.set(runs),
      error: () => this.reportRuns.set([]),
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

  refreshWebhook(): void {
    this.integrations.getWebhookStatus().subscribe({
      next: (s) => this.webhook.set(s),
      error: () => this.webhook.set(null),
    });
  }

  registerWebhook(): void {
    this.tgBusy.set(true);
    this.tgMessage.set(null);
    this.integrations.registerWebhook().subscribe({
      next: (r) => {
        this.tgOk.set(r.ok);
        this.tgMessage.set(r.detail + (r.webhook_url ? ` — ${r.webhook_url}` : ''));
        this.tgBusy.set(false);
        this.loadTelegram();
      },
      error: (err) => {
        this.tgOk.set(false);
        this.tgMessage.set(err?.error?.detail ?? 'Webhook register failed');
        this.tgBusy.set(false);
      },
    });
  }

  deleteWebhook(): void {
    this.tgBusy.set(true);
    this.tgMessage.set(null);
    this.integrations.deleteWebhook().subscribe({
      next: (r) => {
        this.tgOk.set(r.ok);
        this.tgMessage.set(r.detail);
        this.tgBusy.set(false);
        this.loadTelegram();
      },
      error: (err) => {
        this.tgOk.set(false);
        this.tgMessage.set(err?.error?.detail ?? 'Webhook disable failed');
        this.tgBusy.set(false);
      },
    });
  }
}
