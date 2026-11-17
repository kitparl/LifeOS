import { DatePipe } from '@angular/common';
import { Component, Input, OnDestroy, OnInit, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { apiErrorMessage } from '../../../core/utils/http';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { SecretInputComponent } from '../../../shared/secret-input/secret-input.component';
import { isJobActive, jobSummary } from '../../running/activity.utils';
import { ImportJob } from '../../running/models/activity.models';
import { ActivityService } from '../../running/services/activity.service';
import { GarminConnectionStatus, IntegrationsService } from '../services/integrations.service';

const REFRESH_MS = 3000;
export const GARMIN_TOKEN_PAGE = 'https://connect.garmin.com/app/settings/personalApiToken';

/** Garmin Personal API: add the key, see the last sync, sync now, or remove the key. */
@Component({
  selector: 'app-garmin-config',
  standalone: true,
  imports: [DatePipe, FormsModule, SecretInputComponent],
  host: { class: 'contents' },
  template: `
    <div id="garmin" class="panel text-sm" data-testid="garmin-card">
      <div class="flex items-start justify-between gap-2">
        <div>
          <p class="font-medium">{{ displayName }}</p>
          <p class="text-gray-600 text-xs mt-1">{{ description }}</p>
        </div>
        @if (config(); as c) {
          <span class="text-xs shrink-0" [style.color]="c.connected ? 'var(--success)' : 'var(--text-muted)'">
            {{ statusLabel() }}
          </span>
        }
      </div>

      @if (config(); as c) {
        @if (c.last_sync_message && !syncing()) {
          <p class="text-xs mt-2" [style.color]="c.last_sync_ok === false ? 'var(--danger)' : 'var(--text-muted)'" data-testid="garmin-last-sync">
            {{ c.last_sync_message }}
            @if (c.last_sync_at) {
              <span> · {{ c.last_sync_at | date: 'medium' }}</span>
            }
          </p>
        }
        @if (c.connected) {
          <div class="flex flex-wrap gap-2 mt-2">
            <button type="button" class="btn-primary text-xs" data-testid="garmin-sync-button" [disabled]="busy() || syncing()" (click)="syncNow()">
              {{ syncing() ? 'Syncing…' : 'Sync now' }}
            </button>
            <button type="button" class="text-xs" style="color: var(--danger)" [disabled]="busy()" (click)="remove()">Remove key</button>
          </div>
          @if (job(); as j) {
            @if (syncing()) {
              <p class="text-xs mt-1" style="color: var(--text-muted)" data-testid="garmin-progress">
                {{ summaryOf(j) }}
                @if (c.synced_through) {
                  <span> · checked up to {{ c.synced_through | date: 'mediumDate' }}</span>
                }
              </p>
            }
          }
        }
      }

      <details class="mt-3 text-xs">
        <summary class="cursor-pointer font-medium">How to connect</summary>
        <ol class="mt-2 list-decimal pl-4 space-y-1" style="color: var(--text-muted)">
          <li>
            Open <a [href]="tokenPage" target="_blank" rel="noopener noreferrer">Garmin Connect → Personal API token</a>
            and create a key. Garmin shows it only once.
          </li>
          <li>Paste it below and choose Save and sync. The first sync pulls the last 12 months and can take a few minutes.</li>
          <li>After that LifeOS syncs once a day (late morning), or whenever you choose Sync now.</li>
          <li>Runs appear in Running, health data in Health. Synced data is not used by AI features.</li>
        </ol>
      </details>

      <details class="mt-3 text-xs" [open]="!config()?.connected">
        <summary class="cursor-pointer font-medium">API key</summary>
        <div class="mt-3 flex flex-col gap-2">
          <div class="flex flex-col gap-1">
            <label class="form-label" for="garmin-key">Garmin personal API key</label>
            <app-secret-input inputId="garmin-key" [(ngModel)]="keyInput" [placeholder]="keyPlaceholder()" autocomplete="off" />
          </div>
          <div class="flex flex-wrap gap-2 mt-1">
            <button type="button" class="btn-primary text-xs" data-testid="garmin-save-button" [disabled]="busy()" (click)="save()">
              {{ busy() ? 'Checking…' : 'Save and sync' }}
            </button>
          </div>
          @if (message()) {
            <p class="text-xs" [style.color]="ok() ? 'var(--success)' : 'var(--danger)'" data-testid="garmin-message">{{ message() }}</p>
          }
        </div>
      </details>
    </div>
  `,
})
export class GarminConfigComponent implements OnInit, OnDestroy {
  private readonly integrations = inject(IntegrationsService);
  private readonly activities = inject(ActivityService);
  private readonly confirm = inject(ConfirmService);

  @Input({ required: true }) displayName = '';
  @Input({ required: true }) description = '';

  readonly connectionsChanged = output<void>();

  readonly tokenPage = GARMIN_TOKEN_PAGE;
  readonly config = signal<GarminConnectionStatus | null>(null);
  readonly job = signal<ImportJob | null>(null);
  readonly syncing = signal(false);
  readonly busy = signal(false);
  readonly message = signal<string | null>(null);
  readonly ok = signal(false);
  keyInput = '';

  summaryOf = jobSummary;
  private timer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.load();
    this.watchLatestJob();
  }

  ngOnDestroy(): void {
    this.clearTimer();
  }

  statusLabel(): string {
    const c = this.config();
    if (!c) return '';
    if (c.connected) return 'Connected';
    if (c.status === 'error') return 'Needs a new key';
    return 'Not connected';
  }

  keyPlaceholder(): string {
    const masked = this.config()?.key_masked;
    return masked ? `Saved: ${masked} (paste a new key to replace it)` : 'Paste your Garmin personal API key';
  }

  load(): void {
    this.integrations.getGarmin().subscribe({
      next: (status) => this.config.set(status),
      error: (err) => this.fail(err, 'Failed to load the Garmin connection'),
    });
  }

  save(): void {
    const key = this.keyInput.trim();
    if (!key) {
      this.ok.set(false);
      this.message.set('Paste a key first');
      return;
    }
    this.busy.set(true);
    this.message.set(null);
    this.integrations.saveGarminKey(key).subscribe({
      next: (status) => {
        this.config.set(status);
        this.keyInput = '';
        this.ok.set(true);
        this.message.set('Key saved. The first sync has started.');
        this.busy.set(false);
        this.connectionsChanged.emit();
        this.watchLatestJob();
      },
      error: (err) => this.fail(err, 'Garmin did not accept this key'),
    });
  }

  syncNow(): void {
    this.message.set(null);
    this.integrations.syncGarmin().subscribe({
      next: (job) => {
        this.job.set(job);
        this.syncing.set(true);
        this.watchLatestJob();
      },
      error: (err) => this.fail(err, 'The sync could not start'),
    });
  }

  async remove(): Promise<void> {
    const ok = await this.confirm.confirm(
      'LifeOS will stop syncing from Garmin and forget the key. You can delete the key on Garmin Connect too.',
      'Remove the Garmin key?',
      { acceptLabel: 'Remove key' },
    );
    if (!ok) return;
    const deleteData = await this.confirm.confirm(
      'Also delete everything imported from Garmin: activities, the runs they created and Garmin health data? ' +
        'Choose Cancel to keep it. Runs you logged by hand keep your notes and get your own distance and time back.',
      'Delete imported Garmin data too?',
      { acceptLabel: 'Delete imported data too' },
    );
    this.busy.set(true);
    this.integrations.disconnectGarmin().subscribe({
      next: () => {
        if (!deleteData) return this.removed('Garmin key removed. Your imported data is kept.');
        this.activities.deleteImportedData(true).subscribe({
          next: () => this.removed('Garmin key removed and imported data deleted.'),
          error: (err) => this.fail(err, 'The key was removed, but the imported data could not be deleted'),
        });
      },
      error: (err) => this.fail(err, 'Failed to remove the Garmin key'),
    });
  }

  private removed(text: string): void {
    this.ok.set(true);
    this.message.set(text);
    this.busy.set(false);
    this.connectionsChanged.emit();
    this.load();
  }

  /** Follow the newest sync-log entry while it runs, then refresh the connection status once. */
  private watchLatestJob(): void {
    this.clearTimer();
    this.activities.listImports({ limit: 1 }).subscribe({
      next: ({ items }) => {
        const latest = items[0] ?? null;
        const running = latest?.origin === 'sync' && isJobActive(latest);
        this.job.set(latest);
        if (running) {
          this.syncing.set(true);
          this.load(); // the connection's "synced through" date shows how far the sync has got
          this.timer = setTimeout(() => this.watchLatestJob(), REFRESH_MS);
        } else if (this.syncing()) {
          this.syncing.set(false);
          this.load();
        }
      },
    });
  }

  private fail(err: unknown, fallback: string): void {
    this.ok.set(false);
    this.message.set(apiErrorMessage(err, fallback));
    this.busy.set(false);
  }

  private clearTimer(): void {
    if (this.timer) clearTimeout(this.timer);
    this.timer = null;
  }
}
