import { Component, computed, input, output } from '@angular/core';
import { PublicPlanView } from '../../models/share.models';
import { COPY } from '../planner-copy';
import { SaveState } from '../planner-store';

/** Trip name and dates, the save status in words, "Final plan", and the owner's shortcut. */
@Component({
  selector: 'app-planner-header',
  standalone: true,
  template: `
    @let v = view();
    <header class="head">
      <div class="title">
        <h1>{{ v.trip.name }}</h1>
        <p class="tp-muted">
          @if (dates()) { {{ dates() }} · }{{ editing() ? copy.yourPlan : v.owner_name }}
        </p>
      </div>
      <div class="side">
        @if (v.is_final) {
          <span class="tp-chip final" data-testid="final-badge">🔒 {{ copy.finalBadge }}</span>
        }
        @if (status()) {
          <span class="save" [attr.data-state]="saveState()" role="status" data-testid="save-state">{{ status() }}</span>
        }
        @if (canUndo()) {
          <button type="button" class="tp-btn tp-btn--quiet" (click)="undo.emit()">↶ {{ copy.undo }}</button>
        }
        <button type="button" class="tp-btn tp-btn--quiet you" (click)="openMe.emit()">{{ copy.tabs.me }}</button>
      </div>
    </header>
  `,
  styles: [
    `
      .head { display: flex; align-items: flex-start; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; }
      .title { min-width: 0; flex: 1; }
      h1 { font-size: 1.625rem; line-height: 1.2; overflow-wrap: anywhere; }
      .side { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
      .final { background: var(--tp-accent); color: var(--tp-on-accent); }
      .save { font-weight: 600; font-size: 0.9375rem; }
      .save[data-state='saved'] { color: var(--tp-ok); }
      .save[data-state='offline'], .save[data-state='error'], .save[data-state='conflict'] { color: var(--tp-warn); }
      @media (max-width: 639px) { .you { display: none; } }
    `,
  ],
})
export class PlannerHeaderComponent {
  readonly view = input.required<PublicPlanView>();
  readonly saveState = input<SaveState>('idle');
  readonly editing = input(false);
  readonly canUndo = input(false);
  readonly undo = output<void>();
  readonly openMe = output<void>();
  readonly copy = COPY;

  readonly dates = computed(() => {
    const { start_date, end_date } = this.view().trip;
    if (!start_date) return '';
    const fmt = (d: string) => new Date(`${d}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
    return end_date && end_date !== start_date ? `${fmt(start_date)} – ${fmt(end_date)}` : fmt(start_date);
  });

  readonly status = computed(() => {
    switch (this.saveState()) {
      case 'saving':
        return COPY.saving;
      case 'saved':
        return `✓ ${COPY.saved}`;
      case 'offline':
        return COPY.offline;
      case 'error':
        return COPY.saveError;
      default:
        return '';
    }
  });
}
