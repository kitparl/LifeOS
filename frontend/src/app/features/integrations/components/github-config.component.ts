import { Component, Input, OnInit, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SecretInputComponent } from '../../../shared/secret-input/secret-input.component';
import {
  GitHubConfigStatus,
  GitHubConfigUpdate,
  IntegrationsService,
} from '../services/integrations.service';

@Component({
  selector: 'app-github-config',
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

      <details class="mt-3 text-xs">
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
              placeholder="kitparl/engineering-notes or https://github.com/…"
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
  `,
})
export class GithubConfigComponent implements OnInit {
  private readonly integrations = inject(IntegrationsService);

  @Input({ required: true }) displayName = '';
  @Input({ required: true }) description = '';

  readonly connectionsChanged = output<void>();

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

  ngOnInit(): void {
    this.loadGitHub();
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
        this.connectionsChanged.emit();
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
}
