import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, inject, signal } from '@angular/core';
import { apiErrorMessage } from '../../../core/utils/http';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { RaceEvent, RunListItem, formatDuration, formatPace } from '../models/running.models';
import { RunningService } from '../services/running.service';

/** Pick the synced run that was this race; the server lists candidates within three days, closest first. */
@Component({
  selector: 'app-race-attach-dialog',
  standalone: true,
  imports: [ModalComponent, DatePipe],
  template: `
    <app-modal [open]="open" title="Attach recorded activity" [maxWidth]="'560px'" [hasFooter]="false" (closed)="closed.emit()">
      <div body class="space-y-3 text-sm">
        @if (loading()) {
          <div class="skeleton" style="width: 200px; height: 14px"></div>
        } @else if (!candidates().length) {
          <p style="color: var(--text-muted)" data-testid="race-attach-empty">
            No synced runs within 3 days of this race.
          </p>
        } @else {
          <p style="color: var(--text-muted)">
            Choose the run that was this race. Its time, route and splits will be shown here; bib, position and
            medal stay as you entered them.
          </p>
          <ul class="space-y-2">
            @for (run of candidates(); track run.id) {
              <li class="flex flex-wrap items-center justify-between gap-2 rounded border border-[var(--xp-border)] p-2">
                <span>
                  <span class="font-medium">{{ run.run_date | date: 'mediumDate' }}</span>
                  <span style="color: var(--text-muted)">
                    · {{ run.distance_km }} km · {{ formatDuration(run.duration_seconds) }}
                    · {{ formatPace(run.pace_min_per_km) }}
                  </span>
                </span>
                <button
                  type="button"
                  class="btn-primary text-xs"
                  [attr.data-testid]="'race-attach-choose-' + run.id"
                  [disabled]="busy()"
                  (click)="attach(run)"
                >Attach</button>
              </li>
            }
          </ul>
        }
        @if (error()) {
          <p class="text-xs" style="color: var(--danger)">{{ error() }}</p>
        }
        <div class="flex justify-end">
          <button type="button" class="btn-secondary text-xs" data-testid="race-attach-cancel-button" (click)="closed.emit()">Cancel</button>
        </div>
      </div>
    </app-modal>
  `,
})
export class RaceAttachDialogComponent implements OnChanges {
  private readonly running = inject(RunningService);

  @Input() open = false;
  @Input({ required: true }) raceId = '';
  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly attached = new EventEmitter<RaceEvent>();

  readonly candidates = signal<RunListItem[]>([]);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly error = signal('');

  readonly formatDuration = formatDuration;
  readonly formatPace = formatPace;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['open']?.currentValue === true && this.raceId) this.load();
  }

  attach(run: RunListItem): void {
    this.busy.set(true);
    this.error.set('');
    this.running.attachRun(this.raceId, run.id).subscribe({
      next: (race) => {
        this.busy.set(false);
        this.attached.emit(race);
      },
      error: (err) => {
        this.error.set(apiErrorMessage(err, 'The run could not be attached'));
        this.busy.set(false);
      },
    });
  }

  private load(): void {
    this.loading.set(true);
    this.error.set('');
    this.candidates.set([]);
    this.running.listRaceCandidates(this.raceId).subscribe({
      next: (runs) => {
        this.candidates.set(runs);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(apiErrorMessage(err, 'Could not load runs for this race'));
        this.loading.set(false);
      },
    });
  }
}
