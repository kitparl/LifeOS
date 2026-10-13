import { Component, computed, input, output } from '@angular/core';
import { PublicPlanView } from '../../models/share.models';
import { formatDuration } from '../../models/travel.models';
import { PlanFacts } from '../plan-route';
import { COPY } from '../planner-copy';
import { SaveState } from '../planner-store';
import { kmText } from './day-section.component';

/** Trip name and dates, the trip at a glance (days, km, time on the road, stops), the save status
 * in words, "Final plan", and actions: Download PDF, Undo, You. */
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
        <button type="button" class="tp-btn tp-btn--quiet" data-testid="download-pdf" [disabled]="pdfBusy()" (click)="pdf.emit()">
          <span aria-hidden="true">⬇</span> {{ pdfBusy() ? copy.makingPdf : copy.downloadPdf }}
        </button>
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
    @if (glance().length) {
      <ul class="glance" data-testid="trip-glance">
        @for (item of glance(); track item.label) {
          <li><strong>{{ item.value }}</strong>{{ ' ' }}<span class="tp-muted">{{ item.label }}</span></li>
        }
      </ul>
    }
    @if (facts()?.approx) { <p class="tp-muted note">{{ copy.estimateNote }}</p> }
  `,
  styles: [
    `
      :host { display: grid; gap: 0.75rem; }
      .head { display: flex; align-items: flex-start; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; }
      .glance { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 0.5rem; }
      .glance li {
        display: grid; padding: 0.5rem 0.875rem; border-radius: var(--tp-radius-sm);
        background: var(--tp-surface); border: 1px solid var(--tp-border); min-width: 6.5rem;
      }
      .glance strong { font-size: var(--tp-text-lg); }
      .glance span { font-size: 0.8125rem; }
      .note { font-size: 0.875rem; }
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
  readonly facts = input<PlanFacts | null>(null);
  readonly pdfBusy = input(false);
  readonly undo = output<void>();
  readonly pdf = output<void>();
  readonly openMe = output<void>();
  readonly copy = COPY;

  readonly dates = computed(() => {
    const { start_date, end_date } = this.view().trip;
    if (!start_date) return '';
    const fmt = (d: string) => new Date(`${d}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });
    return end_date && end_date !== start_date ? `${fmt(start_date)} – ${fmt(end_date)}` : fmt(start_date);
  });

  readonly glance = computed(() => {
    const f = this.facts();
    if (!f || !f.days.length) return [];
    const items = [{ value: String(f.days.length), label: COPY.dayWord(f.days.length) }];
    if (f.meters) items.push({ value: kmText(f.meters, f.approx), label: this.howMeasured(f) });
    if (f.seconds) items.push({ value: formatDuration(f.seconds)!, label: COPY.onTheRoad });
    if (f.places) items.push({ value: String(f.places), label: COPY.stopWord(f.places) });
    return items;
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

  private howMeasured(f: PlanFacts): string {
    if (!f.approx) return COPY.byRoad;
    return f.days.some((d) => d.road) ? COPY.partlyByRoad : COPY.straightLine;
  }
}
