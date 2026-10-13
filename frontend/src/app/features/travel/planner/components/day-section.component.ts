import { CdkDrag, CdkDragDrop, CdkDropList } from '@angular/cdk/drag-drop';
import { Component, computed, input, output } from '@angular/core';
import { PlanDay, PlanStop } from '../../models/share.models';
import { directionsUrl } from '../../utils/google-links';
import { COPY } from '../planner-copy';
import { PlannerStopCardComponent } from './stop-card.component';

export function dayColorVar(index: number): string {
  return `var(--tp-day-${(index % 8) + 1})`;
}

/** One day: its colour and number (never colour alone), its stops, and one big "Add a place". */
@Component({
  selector: 'app-planner-day',
  standalone: true,
  imports: [CdkDropList, CdkDrag, PlannerStopCardComponent],
  template: `
    <section class="day" [id]="'tp-day-' + index()" [attr.aria-labelledby]="'tp-day-title-' + index()">
      <header>
        <span class="badge" [style.background]="color()" aria-hidden="true">{{ index() + 1 }}</span>
        <div class="heading">
          <h3 [id]="'tp-day-title-' + index()">{{ copy.day(index() + 1) }}@if (day().title) { · {{ day().title }} }</h3>
          @if (date()) { <p class="tp-muted">{{ date() }}</p> }
        </div>
        @if (routeUrl()) {
          <a class="route" [href]="routeUrl()" target="_blank" rel="noopener noreferrer">{{ copy.openDayInMaps }}</a>
        }
      </header>
      @if (day().notes) { <p class="tp-muted notes">{{ day().notes }}</p> }
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
            <app-planner-stop-card
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
      header { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
      .badge {
        display: grid; place-items: center; width: 2.25rem; height: 2.25rem; border-radius: 50%;
        color: var(--tp-on-day); font-weight: 800;
      }
      .heading { flex: 1; min-width: 8rem; }
      h3 { font-size: var(--tp-text-xl); }
      .route { color: var(--tp-accent); font-weight: 600; min-height: var(--tp-tap); display: inline-flex; align-items: center; }
      .notes { white-space: pre-line; }
      .stops { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.5rem; min-height: 0.5rem; }
      .empty { padding: 0.75rem; border: 2px dashed var(--tp-border); border-radius: var(--tp-radius); }
      .actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      .add { flex: 1; min-height: 3.25rem; border-style: dashed; border-width: 2px; font-size: var(--tp-text-lg); }
      .cdk-drag-preview { border-radius: var(--tp-radius); box-shadow: 0 12px 28px rgb(0 0 0 / 0.25); }
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
  readonly add = output<void>();
  readonly openStop = output<PlanStop>();
  readonly nudge = output<{ index: number; direction: -1 | 1 }>();
  readonly dropped = output<CdkDragDrop<number>>();
  readonly removeDay = output<void>();
  readonly copy = COPY;

  readonly color = computed(() => dayColorVar(this.index()));
  readonly routeUrl = computed(() => {
    const points = this.day().stops.flatMap((s) => (s.place ? [{ lat: s.place.lat, lng: s.place.lng }] : []));
    return points.length >= 2 ? directionsUrl(points) : null;
  });
}
