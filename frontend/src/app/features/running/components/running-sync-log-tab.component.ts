import { DatePipe } from '@angular/common';
import { Component, EventEmitter, OnDestroy, OnInit, Output, inject, signal } from '@angular/core';
import { apiErrorMessage } from '../../../core/utils/http';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { ListPaginatorComponent } from '../../../shared/pagination/list-paginator.component';
import { isJobActive, jobSummary } from '../activity.utils';
import { ImportJob, ImportedSummary } from '../models/activity.models';
import { ActivityService } from '../services/activity.service';

const REFRESH_MS = 3000;

/** The sync log: every import with its counts and failures, plus removal of everything imported. */
@Component({
  selector: 'app-running-sync-log-tab',
  standalone: true,
  imports: [DatePipe, ListPaginatorComponent],
  host: { class: 'contents' },
  template: `
    <div class="panel text-sm space-y-2" data-testid="sync-log-summary">
      @if (summary(); as s) {
        <p>
          <span class="font-semibold">{{ s.activities }}</span> imported
          {{ s.activities === 1 ? 'activity' : 'activities' }}
          <span style="color: var(--text-muted)">
            · {{ s.runs_created }} {{ s.runs_created === 1 ? 'run' : 'runs' }} created
            · {{ s.runs_merged_into_manual }} of your own {{ s.runs_merged_into_manual === 1 ? 'run' : 'runs' }} matched
          </span>
        </p>
      }
      @if (message()) {
        <p class="text-xs" style="color: var(--text-muted)" data-testid="sync-log-message">{{ message() }}</p>
      }
      @if (error()) {
        <p class="text-xs" style="color: var(--danger)">{{ error() }}</p>
      }
      <button
        type="button"
        class="btn-danger text-xs"
        data-testid="sync-log-delete-button"
        [disabled]="busy() || !(summary()?.activities || summary()?.health_days)"
        (click)="deleteImported()"
      >Delete imported data</button>
    </div>

    <div class="panel !p-0 overflow-hidden">
      @if (loading()) {
        <div class="empty-state"><div class="skeleton" style="width: 160px; height: 14px"></div></div>
      } @else if (total() === 0) {
        <div class="empty-state">
          <p class="empty-state__title">No imports yet</p>
          <p class="empty-state__desc">
            Use Import to add Garmin activity files, or connect Garmin in Integrations. Each import and sync is listed here.
          </p>
        </div>
      } @else {
        <div class="overflow-x-auto">
          <table class="w-full text-sm" style="min-width: 520px" data-testid="sync-log-table">
            <thead>
              <tr>
                <th class="px-3 py-2 text-left">When</th>
                <th class="px-3 py-2 text-left">Source</th>
                <th class="px-3 py-2 text-left">Status</th>
                <th class="px-3 py-2 text-left">Result</th>
              </tr>
            </thead>
            <tbody>
              @for (job of jobs(); track job.id) {
                <tr style="border-bottom: 1px solid var(--border)">
                  <td class="px-3 py-2 align-top">{{ job.created_at | date: 'medium' }}</td>
                  <td class="px-3 py-2 align-top">{{ job.origin === 'sync' ? 'Garmin sync' : 'Upload' }}</td>
                  <td class="px-3 py-2 align-top">
                    <span
                      class="badge"
                      [class.badge--success]="job.status === 'finished'"
                      [class.badge--warning]="active(job)"
                      [class.badge--default]="job.status === 'interrupted'"
                    >{{ statusLabel(job) }}</span>
                  </td>
                  <td class="px-3 py-2">
                    {{ summaryOf(job) }}
                    @if (job.error) {
                      <p class="text-xs" style="color: var(--danger)">{{ job.error }}</p>
                    }
                    @if (job.errors.length) {
                      <details class="text-xs mt-1">
                        <summary class="cursor-pointer">{{ job.errors.length }} failed {{ job.errors.length === 1 ? 'file' : 'files' }}</summary>
                        <ul class="mt-1 space-y-0.5">
                          @for (e of job.errors; track $index) {
                            <li>{{ e.name }} — {{ e.reason }}</li>
                          }
                        </ul>
                      </details>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        <app-list-paginator [total]="total()" [pageSize]="pageSize" [currentPage]="page()" (pageChange)="setPage($event)" />
      }
    </div>
  `,
})
export class RunningSyncLogTabComponent implements OnInit, OnDestroy {
  private readonly activities = inject(ActivityService);
  private readonly confirm = inject(ConfirmService);

  /** Emitted after imported data was deleted so the page can reload runs and stats. */
  @Output() readonly dataChanged = new EventEmitter<void>();

  readonly pageSize = 25;
  readonly jobs = signal<ImportJob[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly summary = signal<ImportedSummary | null>(null);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly message = signal('');
  readonly error = signal('');

  private timer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.load();
  }

  ngOnDestroy(): void {
    this.clearTimer();
  }

  active = isJobActive;
  summaryOf = jobSummary;

  statusLabel(job: ImportJob): string {
    return { queued: 'Waiting', running: 'In progress', finished: 'Finished', failed: 'Failed', interrupted: 'Interrupted' }[
      job.status
    ];
  }

  setPage(page: number): void {
    this.page.set(page);
    this.load();
  }

  load(): void {
    this.clearTimer();
    this.loading.set(this.jobs().length === 0);
    const offset = (this.page() - 1) * this.pageSize;
    this.activities.listImports({ limit: this.pageSize, offset }).subscribe({
      next: ({ items, total }) => {
        this.jobs.set(items);
        this.total.set(total);
        this.loading.set(false);
        if (items.some(isJobActive)) this.timer = setTimeout(() => this.load(), REFRESH_MS);
      },
      error: () => this.loading.set(false),
    });
    this.activities.getImportedSummary().subscribe({ next: (s) => this.summary.set(s) });
  }

  async deleteImported(): Promise<void> {
    const s = this.summary();
    if (!s || (s.activities === 0 && s.health_days === 0)) return;
    const ok = await this.confirm.confirm(
      `Delete ${s.activities} imported ${s.activities === 1 ? 'activity' : 'activities'}? ` +
        'Runs created by imports are removed. Runs you logged by hand keep your notes, shoes and weather ' +
        'and get your own distance and time back. Races linked to an imported run are unlinked. ' +
        'The import log stays.',
      'Delete imported Garmin data',
      { acceptLabel: 'Delete imported data' },
    );
    if (!ok) return;
    // Health data an import stored is a separate choice; data you entered by hand is never deleted.
    const includeHealth =
      s.health_days > 0 &&
      (await this.confirm.confirm(
        `Also delete the ${s.health_days} ${s.health_days === 1 ? 'day' : 'days'} of Garmin health data ` +
          '(sleep, heart rate and so on)? Choose Cancel to keep it. Health data you entered yourself is never deleted.',
        'Delete Garmin health data too?',
        { acceptLabel: 'Delete health data too' },
      ));
    this.busy.set(true);
    this.error.set('');
    this.activities.deleteImportedData(includeHealth).subscribe({
      next: (r) => {
        this.message.set(
          `Deleted ${r.activities_deleted} activities and ${r.runs_deleted} runs; ` +
            `${r.runs_restored} of your own runs restored; ${r.races_detached} races unlinked` +
            (r.health_days_deleted ? `; ${r.health_days_deleted} days of Garmin health data deleted.` : '.'),
        );
        this.busy.set(false);
        this.dataChanged.emit();
        this.load();
      },
      error: (err) => {
        this.error.set(apiErrorMessage(err, 'The imported data could not be deleted'));
        this.busy.set(false);
      },
    });
  }

  private clearTimer(): void {
    if (this.timer) clearTimeout(this.timer);
    this.timer = null;
  }
}
