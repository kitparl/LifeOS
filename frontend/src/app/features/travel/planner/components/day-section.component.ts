import { CdkDrag, CdkDragDrop, CdkDropList } from '@angular/cdk/drag-drop';
import { Component, computed, input, output } from '@angular/core';
import { PlanDay, PlanStop } from '../../models/share.models';
import { formatDistance, formatDuration } from '../../models/travel.models';
import { routeLinks } from '../../utils/google-links';
import { DayFacts, StopLeg } from '../plan-route';
import { COPY } from '../planner-copy';
import { PlannerStopCardComponent } from './stop-card.component';

export function dayColorVar(index: number): string {
  return `var(--tp-day-${(index % 8) + 1})`;
}

/** "~16.9 km" (straight-line estimate) or "51.0 km" (by road). */
export function kmText(meters: number, approx: boolean): string {
  return `${approx ? '~' : ''}${formatDistance(meters)}`;
}

/**
 * One day as a timeline, like the PDF guide: its colour and number (never colour alone), a summary
 * (km, time on the road, stops, where you sleep), the day's route in Google Maps, and its stops
 * joined by a line with how far each one is from the last. One big "Add a place".
 */
@Component({
  selector: 'app-planner-day',
  standalone: true,
  imports: [CdkDropList, CdkDrag, PlannerStopCardComponent],
  template: `
    <section class="day" [id]="'tp-day-' + index()" [attr.aria-labelledby]="'tp-day-title-' + index()" [style.--day]="color()">
      <header>
        <span class="badge" aria-hidden="true">{{ index() + 1 }}</span>
        <div class="heading">
          <h3 [id]="'tp-day-title-' + index()">{{ copy.day(index() + 1) }}@if (day().title) { · {{ day().title }} }</h3>
          @if (date()) { <p class="tp-muted">{{ date() }}</p> }
        </div>
      </header>
      @if (summary()) { <p class="summary" data-testid="day-summary">{{ summary() }}</p> }
      @if (day().notes) { <p class="tp-muted notes">{{ day().notes }}</p> }
      @if (links().length || askRoad()) {
        <div class="route">
          @if (links().length === 1) {
            <a [href]="links()[0].url" target="_blank" rel="noopener noreferrer" data-testid="day-route">{{ copy.openDayInMaps }}</a>
          } @else if (links().length > 1) {
            <span class="tp-muted">{{ copy.openDayInMaps }}:</span>
            @for (link of links(); track link.url; let n = $index) {
              <a [href]="link.url" target="_blank" rel="noopener noreferrer" data-testid="day-route">{{ copy.routePart(n + 1, link.first, link.last) }}</a>
            }
          }
          @if (askRoad()) {
            <button type="button" class="tp-btn road" data-testid="road-km" [disabled]="routing()" (click)="roadKm.emit()">
              <span aria-hidden="true">🚗</span> {{ routing() ? copy.gettingRoadKm : copy.roadKm }}
            </button>
          }
        </div>
      }
      <ol
        class="stops"
        cdkDropList
        [id]="'tp-day-list-' + index()"
        [cdkDropListData]="index()"
        [cdkDropListDisabled]="!editable()"
        (cdkDropListDropped)="dropped.emit($event)"
      >
        @for (stop of day().stops; track stop.id; let i = $index; let isFirst = $first; let isLast = $last) {
          <li cdkDrag [cdkDragData]="i">
            @if (facts()?.legs?.[stop.id]; as leg) {
              <p class="leg" data-testid="stop-leg">{{ legText(leg) }}</p>
            }
            <span class="dot" aria-hidden="true">{{ i + 1 }}</span>
            <app-planner-stop-card
              class="stop"
              [stop]="stop"
              [index]="i"
              [first]="isFirst && index() === 0"
              [last]="isLast && index() === dayCount() - 1"
              [color]="color()"
              [editable]="editable()"
              (open)="openStop.emit(stop)"
              (nudge)="nudge.emit({ index: i, direction: $event })"
            />
          </li>
        } @empty {
          <li class="empty tp-muted">{{ copy.emptyDay }}</li>
        }
      </ol>
      @if (editable()) {
        <div class="actions">
          <button type="button" class="tp-btn add" data-testid="add-place" (click)="add.emit()">
            <span aria-hidden="true">＋</span> {{ copy.addPlace }}
          </button>
          @if (!day().stops.length) {
            <button type="button" class="tp-btn tp-btn--quiet" (click)="removeDay.emit()">{{ copy.removeDay(index() + 1) }}</button>
          }
        </div>
      }
    </section>
  `,
  styles: [
    `
      .day { display: grid; gap: 0.75rem; }
      header { display: flex; align-items: center; gap: 0.75rem; }
      .badge {
        display: grid; place-items: center; flex: none; width: 2.5rem; height: 2.5rem; border-radius: 50%;
        background: var(--day); color: var(--tp-on-day); font-weight: 800; font-size: 1.125rem;
      }
      .heading { flex: 1; min-width: 0; }
      h3 { font-size: var(--tp-text-xl); overflow-wrap: anywhere; }
      .summary { font-weight: 600; }
      .notes { white-space: pre-line; }
      .route { display: flex; flex-wrap: wrap; align-items: center; gap: 0.25rem 1rem; }
      .route a { display: inline-flex; align-items: center; min-height: var(--tp-tap); color: var(--tp-accent); font-weight: 600; }
      .road { font-size: 0.9375rem; }
      .stops { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.5rem; min-height: 0.5rem; }
      .stops li:not(.empty) {
        position: relative; display: grid; grid-template-columns: 2rem minmax(0, 1fr); column-gap: 0.5rem; align-items: start;
      }
      /* The day's line, joining one stop to the next. */
      .stops li:not(.empty)::before {
        content: ''; position: absolute; left: calc(1rem - 1px); top: 0; bottom: -0.5rem; width: 2px;
        background: var(--day); opacity: 0.4;
      }
      .stops li:not(.empty):last-child::before { bottom: auto; height: 1.5rem; }
      .leg { grid-column: 2; margin: 0; padding: 0 0 0.125rem; font-size: 0.875rem; color: var(--tp-muted); font-weight: 600; }
      .dot {
        grid-column: 1; position: relative; justify-self: center; margin-top: 0.75rem; display: grid; place-items: center;
        width: 1.75rem; height: 1.75rem; border-radius: 50%; background: var(--day); color: var(--tp-on-day);
        font-weight: 800; font-size: 0.875rem; box-shadow: 0 0 0 3px var(--tp-bg);
      }
      .stop { grid-column: 2; min-width: 0; }
      .empty { padding: 0.75rem; border: 2px dashed var(--tp-border); border-radius: var(--tp-radius); }
      .actions { display: flex; flex-wrap: wrap; gap: 0.5rem; padding-left: 2.5rem; }
      .add { flex: 1; min-height: 3.25rem; border-style: dashed; border-width: 2px; font-size: var(--tp-text-lg); }
      .cdk-drag-preview { border-radius: var(--tp-radius); box-shadow: 0 12px 28px rgb(0 0 0 / 0.25); }
      .cdk-drag-preview::before, .cdk-drag-placeholder::before { display: none; }
      .cdk-drag-placeholder { opacity: 0.35; }
      .cdk-drag-animating, .stops.cdk-drop-list-dragging li:not(.cdk-drag-placeholder) { transition: transform var(--tp-ease); }
    `,
  ],
})
export class PlannerDayComponent {
  readonly day = input.required<PlanDay>();
  readonly index = input.required<number>();
  readonly dayCount = input.required<number>();
  readonly date = input<string | null>(null);
  readonly editable = input(false);
  /** Distances for this day (see `plan-route.ts`). */
  readonly facts = input<DayFacts | null>(null);
  readonly routing = input(false);
  readonly add = output<void>();
  readonly openStop = output<PlanStop>();
  readonly nudge = output<{ index: number; direction: -1 | 1 }>();
  readonly dropped = output<CdkDragDrop<number>>();
  readonly removeDay = output<void>();
  readonly roadKm = output<void>();
  readonly copy = COPY;

  readonly color = computed(() => dayColorVar(this.index()));
  /** Like the PDF: from where the trip was before this day, through every place of the day. */
  readonly links = computed(() => {
    const facts = this.facts();
    if (facts?.chain.length) return routeLinks(facts.chain.map(([lat, lng]) => ({ lat, lng })), facts.mode);
    return [];
  });
  readonly askRoad = computed(() => this.editable() && !!this.facts()?.canRoute);
  readonly summary = computed(() => {
    const f = this.facts();
    if (!f) return '';
    const legs = Object.keys(f.legs).length;
    const parts: string[] = [];
    if (legs) parts.push(`${kmText(f.meters, f.approx)} ${f.approx ? `(${COPY.straightLine})` : COPY.byRoad}`);
    if (f.seconds) parts.push(`${COPY.about(formatDuration(f.seconds)!)} ${COPY.onTheRoad}`);
    if (f.places) parts.push(`${f.places} ${COPY.stopWord(f.places)}`);
    if (f.stays.length) parts.push(COPY.sleepAt(f.stays.join(', ')));
    return parts.join(' · ');
  });

  legText(leg: StopLeg): string {
    const time = leg.seconds ? ` · ${COPY.about(formatDuration(leg.seconds)!)}` : '';
    return `${leg.approx ? '' : '🚗 '}${kmText(leg.meters, leg.approx)}${time} ${COPY.fromPlace(leg.fromName)}`;
  }
}
