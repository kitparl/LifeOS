import { DatePipe } from '@angular/common';
import { Component, Input, OnDestroy, OnInit, computed, inject, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { apiErrorMessage } from '../../../core/utils/http';
import { isJobActive, jobSummary } from '../../running/activity.utils';
import { GarminSyncMonths, ImportJob } from '../../running/models/activity.models';
import { ActivityService } from '../../running/services/activity.service';
import { GarminConnectionStatus, GarminSyncScope, IntegrationsService } from '../services/integrations.service';

const REFRESH_MS = 3000;
export const GARMIN_SYNC_MONTHS: readonly GarminSyncMonths[] = [1, 3, 6, 9, 12];

export function garminMonthsLabel(months: GarminSyncMonths): string {
  return months === 1 ? 'Last 1 month' : `Last ${months} months`;
}

/**
 * Range picker + Sync button for Garmin, with progress while a sync runs. Renders nothing until Garmin is
 * connected. `scope` limits the sync: Health pulls only health data, Running only activities.
 */
@Component({
  selector: 'app-garmin-sync',
  standalone: true,
  imports: [DatePipe, FormsModule],
  template: `
    @if (status()?.connected) {
      <div class="flex flex-col gap-1" [class.items-end]="alignEnd">
        <div class="flex flex-wrap items-center gap-2">
          <select
            class="input-field text-xs !w-auto"
            aria-label="What to sync from Garmin"
            data-testid="garmin-sync-range"
            [(ngModel)]="months"
            [disabled]="syncing()"
          >
            @if (cursor()) {
              <option [ngValue]="null">Since last sync</option>
            }
            @for (m of monthOptions; track m) {
              <option [ngValue]="m">{{ monthsLabel(m) }}</option>
            }
          </select>
          <button type="button" class="btn-secondary text-xs" data-testid="garmin-sync-button" [disabled]="syncing()" (click)="syncNow()">
            {{ syncing() ? 'Syncing…' : buttonLabel() }}
          </button>
        </div>
        @if (syncing() && job(); as j) {
          <p class="text-xs" style="color: var(--text-muted)" data-testid="garmin-progress">
            {{ summaryOf(j) }}
            @if (scope !== 'activities' && status()?.synced_through; as through) {
              <span> · checked up to {{ through | date: 'mediumDate' }}</span>
            }
          </p>
        }
        @if (error()) {
          <p class="text-xs" style="color: var(--danger)" data-testid="garmin-sync-error">{{ error() }}</p>
        } @else if (showResult && !syncing() && result()) {
          <p class="text-xs" [style.color]="result()?.ok ? 'var(--text-muted)' : 'var(--danger)'" data-testid="garmin-sync-result">
            {{ result()?.text }}
          </p>
        }
      </div>
    }
  `,
})
export class GarminSyncComponent implements OnInit, OnDestroy {
  private readonly integrations = inject(IntegrationsService);
  private readonly activities = inject(ActivityService);

  @Input() scope: GarminSyncScope = 'all';
  /** Right-align the progress line under the button (page headers). */
  @Input() alignEnd = false;
  /** Show the outcome of a sync that ends here (the Integrations card shows it itself). */
  @Input() showResult = true;

  /** A sync started or ended (the Integrations card hides its last result meanwhile). */
  readonly syncingChange = output<boolean>();
  /** A sync ended: reload whatever it may have changed. */
  readonly finished = output<void>();

  readonly monthOptions = GARMIN_SYNC_MONTHS;
  readonly monthsLabel = garminMonthsLabel;
  readonly summaryOf = jobSummary;
  readonly status = signal<GarminConnectionStatus | null>(null);
  readonly job = signal<ImportJob | null>(null);
  readonly syncing = signal(false);
  readonly error = signal<string | null>(null);
  readonly result = signal<{ text: string; ok: boolean } | null>(null);
  /** "Since last sync" is offered only once this scope has synced something. */
  readonly cursor = computed(() => {
    const s = this.status();
    if (!s) return null;
    return this.scope === 'activities' ? s.activities_synced_through : s.synced_through;
  });
  readonly buttonLabel = computed(() => (this.scope === 'all' ? 'Sync now' : 'Sync Garmin'));
  /** null: continue from the last synced day. */
  months: GarminSyncMonths | null = null;

  private timer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.loadStatus();
    this.watchLatestJob();
  }

  ngOnDestroy(): void {
    this.clearTimer();
  }

  syncNow(): void {
    this.error.set(null);
    this.result.set(null);
    this.integrations.syncGarmin(this.months, this.scope).subscribe({
      next: (job) => {
        this.job.set(job);
        this.setSyncing(true);
        this.watchLatestJob();
      },
      error: (err) => this.error.set(apiErrorMessage(err, 'The sync could not start')),
    });
  }

  private loadStatus(afterSync = false): void {
    this.integrations.getGarmin().subscribe({
      next: (status) => {
        this.status.set(status);
        if (!this.cursor() && this.months === null) this.months = 1;
        if (afterSync && status.last_sync_message) {
          this.result.set({ text: status.last_sync_message, ok: status.last_sync_ok !== false });
        }
      },
      error: () => this.status.set(null), // not connected or unavailable: show nothing
    });
  }

  /** Follow the newest sync-log entry while it runs, then refresh once (also after a new key starts one). */
  watchLatestJob(): void {
    this.clearTimer();
    this.activities.listImports({ limit: 1 }).subscribe({
      next: ({ items }) => {
        const latest = items[0] ?? null;
        const running = latest?.origin === 'sync' && isJobActive(latest);
        this.job.set(latest);
        if (running) {
          this.setSyncing(true);
          this.loadStatus(); // "checked up to" shows how far the sync has got
          this.timer = setTimeout(() => this.watchLatestJob(), REFRESH_MS);
        } else if (this.syncing()) {
          this.setSyncing(false);
          this.loadStatus(true);
          this.finished.emit();
        }
      },
    });
  }

  private setSyncing(value: boolean): void {
    if (this.syncing() === value) return;
    this.syncing.set(value);
    this.syncingChange.emit(value);
  }

  private clearTimer(): void {
    if (this.timer) clearTimeout(this.timer);
    this.timer = null;
  }
}
