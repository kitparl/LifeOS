import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges, inject, signal } from '@angular/core';
import { Subscription, switchMap, takeWhile, timer } from 'rxjs';
import { apiErrorMessage } from '../../../core/utils/http';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { isJobActive, jobSummary } from '../activity.utils';
import { ImportJob, ImportRange } from '../models/activity.models';
import { ActivityService } from '../services/activity.service';

const POLL_MS = 1500;

/** Upload Garmin .fit files or an export .zip and follow the import until it finishes. */
@Component({
  selector: 'app-running-import-dialog',
  standalone: true,
  imports: [ModalComponent],
  template: `
    <app-modal [open]="open" title="Import from Garmin" [maxWidth]="'560px'" (closed)="close()">
      <div body class="space-y-3 text-sm">
        @if (job(); as j) {
            <div class="space-y-2" data-testid="import-dialog-progress">
              <p class="font-medium">
                @switch (j.status) {
                  @case ('queued') { Waiting to start… }
                  @case ('running') { Importing… }
                  @case ('finished') { Import finished }
                  @case ('interrupted') { Import interrupted }
                  @default { Import failed }
                }
              </p>
              <p>{{ summary(j) }}</p>
              @if (j.status === 'finished' && j.runs_created) {
                <p style="color: var(--text-muted)">
                  {{ j.runs_created }} new {{ j.runs_created === 1 ? 'run' : 'runs' }} added to your log.
                </p>
              }
              @if (j.runs_matched) {
                <p style="color: var(--text-muted)">
                  {{ j.runs_matched }} {{ j.runs_matched === 1 ? 'run' : 'runs' }} you logged by hand matched an
                  activity; your notes, shoes and weather were kept.
                </p>
              }
              @if (j.status === 'interrupted') {
                <p style="color: var(--text-muted)">
                  The server restarted during the import. Upload the files again; activities already imported are skipped.
                </p>
              }
              @if (j.error) {
                <p style="color: var(--danger)">{{ j.error }}</p>
              }
              @if (j.errors.length) {
                <div class="rounded border border-[var(--xp-border)] p-2" style="max-height: 10rem; overflow: auto">
                  <p class="text-xs font-semibold mb-1">Files that could not be imported</p>
                  <ul class="text-xs space-y-0.5">
                    @for (e of j.errors; track $index) {
                      <li>{{ e.name }} — {{ e.reason }}</li>
                    }
                  </ul>
                </div>
              }
            </div>
        } @else {
          <p style="color: var(--text-muted)">
            Upload activity files (.fit) or the .zip from Garmin's account data export. Activities you have
            already imported are skipped, so it is safe to upload the same files again.
          </p>
          <div>
            <label class="form-label" for="import-files">Files</label>
            <input
              id="import-files"
              data-testid="import-dialog-files-input"
              class="input-field mt-1"
              type="file"
              multiple
              accept=".fit,.zip"
              (change)="onFiles($event)"
            />
          </div>
          <div>
            <label class="form-label" for="import-range">Which activities</label>
            <select
              id="import-range"
              data-testid="import-dialog-range-select"
              class="input-field mt-1"
              [value]="range()"
              (change)="onRange($event)"
            >
              <option value="12m">Last 12 months</option>
              <option value="all">Everything</option>
            </select>
          </div>
          @if (error()) {
            <p class="text-xs" style="color: var(--danger)" data-testid="import-dialog-error">{{ error() }}</p>
          }
        }
      </div>
      <div footer class="flex flex-wrap justify-end gap-2">
        @if (!job()) {
          <button type="button" class="btn-secondary text-xs" data-testid="import-dialog-cancel-button" (click)="close()">Cancel</button>
          <button
            type="button"
            class="btn-primary text-xs"
            data-testid="import-dialog-start-button"
            [disabled]="busy() || !files().length"
            (click)="start()"
          >{{ busy() ? 'Uploading…' : 'Start import' }}</button>
        } @else {
          <button type="button" class="btn-primary text-xs" data-testid="import-dialog-done-button" (click)="close()">
            {{ active() ? 'Close (keeps running)' : 'Done' }}
          </button>
        }
      </div>
    </app-modal>
  `,
})
export class RunningImportDialogComponent implements OnChanges, OnDestroy {
  private readonly activities = inject(ActivityService);

  @Input() open = false;
  @Output() readonly closed = new EventEmitter<void>();
  /** Emitted when a started import is no longer in progress, so the page can reload. */
  @Output() readonly imported = new EventEmitter<void>();

  readonly files = signal<File[]>([]);
  readonly range = signal<ImportRange>('12m');
  readonly job = signal<ImportJob | null>(null);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly summary = jobSummary;

  private poll: Subscription | null = null;

  active(): boolean {
    return isJobActive(this.job());
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['open']?.currentValue === true) this.reset();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  onFiles(event: Event): void {
    this.files.set(Array.from((event.target as HTMLInputElement).files ?? []));
  }

  onRange(event: Event): void {
    this.range.set((event.target as HTMLSelectElement).value === 'all' ? 'all' : '12m');
  }

  start(): void {
    if (!this.files().length || this.busy()) return;
    this.busy.set(true);
    this.error.set('');
    this.activities.startImport(this.files(), this.range()).subscribe({
      next: (job) => {
        this.job.set(job);
        this.busy.set(false);
        this.follow(job);
      },
      error: (err) => {
        this.error.set(apiErrorMessage(err, 'The import could not be started'));
        this.busy.set(false);
      },
    });
  }

  close(): void {
    this.stopPolling();
    this.closed.emit();
  }

  private follow(first: ImportJob): void {
    this.stopPolling();
    if (!isJobActive(first)) {
      this.imported.emit();
      return;
    }
    this.poll = timer(POLL_MS, POLL_MS)
      .pipe(
        switchMap(() => this.activities.getImport(first.id)),
        takeWhile((job) => isJobActive(job), true),
      )
      .subscribe({
        next: (job) => this.job.set(job),
        error: () => this.error.set('Lost contact with the server. The import continues; see the Imports tab.'),
        complete: () => this.imported.emit(),
      });
  }

  private stopPolling(): void {
    this.poll?.unsubscribe();
    this.poll = null;
  }

  private reset(): void {
    this.stopPolling();
    this.files.set([]);
    this.range.set('12m');
    this.job.set(null);
    this.busy.set(false);
    this.error.set('');
  }
}
