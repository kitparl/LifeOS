import { Component, computed, effect, input, output, signal, untracked } from '@angular/core';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { VersionRow } from '../models/share.models';

/** "Lock this version": the final plan for everyone with the link, optionally applied to the trip. */
@Component({
  selector: 'app-share-lock-dialog',
  standalone: true,
  imports: [ModalComponent],
  template: `
    <app-modal [open]="!!version()" title="Lock this version?" (closed)="closed.emit()">
      <div body class="space-y-3 text-sm">
        @if (version(); as v) {
          <p>
            <strong>{{ v.label }}</strong> becomes the final plan. Everyone with the link sees it read-only and
            nobody can change their plan until you unlock.
          </p>
          <label class="flex items-start gap-2">
            <input type="checkbox" data-testid="lock-apply" [checked]="apply()" (change)="apply.set(!apply())" />
            <span>
              Also apply this to my trip
              <span class="block text-xs" style="color: var(--text-muted)">
                Your trip's days and stops are replaced by this plan. A backup of your current trip is saved first, so you can undo it.
              </span>
            </span>
          </label>
          @if (apply() && endDateNote()) {
            <p class="text-xs" data-testid="lock-end-date">{{ endDateNote() }}</p>
          }
        }
      </div>
      <div footer class="flex justify-end gap-2">
        <button type="button" class="btn-secondary" (click)="closed.emit()">Cancel</button>
        <button type="button" class="btn-primary" data-testid="lock-confirm" [disabled]="busy()" (click)="confirmed.emit(apply())">Lock</button>
      </div>
    </app-modal>
  `,
})
export class ShareLockDialogComponent {
  readonly version = input<VersionRow | null>(null);
  readonly busy = input(false);
  /** The trip's day count and start date, to warn when applying changes the end date (requirements D-13). */
  readonly tripDays = input(0);
  readonly tripStart = input<string | null>(null);
  readonly confirmed = output<boolean>();
  readonly closed = output<void>();

  readonly apply = signal(true);

  readonly endDateNote = computed(() => {
    const v = this.version();
    const start = this.tripStart();
    if (!v || !start || v.summary.days === this.tripDays() || v.summary.days === 0) return null;
    const end = new Date(`${start}T00:00:00`);
    end.setDate(end.getDate() + v.summary.days - 1);
    return `Your trip will have ${v.summary.days} days, so its end date changes to ${end.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}.`;
  });

  constructor() {
    // Each time the dialog opens for a version, "apply" starts ticked again (the default).
    effect(() => {
      if (this.version()) untracked(() => this.apply.set(true));
    });
  }
}
