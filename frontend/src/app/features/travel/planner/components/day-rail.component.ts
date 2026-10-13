import { Component, input, output } from '@angular/core';
import { PlanDay } from '../../models/share.models';
import { PlanFacts } from '../plan-route';
import { COPY } from '../planner-copy';
import { dayColorVar, kmText } from './day-section.component';

/** Desktop left column: every day with its colour, number, stops and km; jumps to it, adds days. */
@Component({
  selector: 'app-planner-day-rail',
  standalone: true,
  template: `
    <nav aria-label="Days">
      <ol>
        @for (day of days(); track $index) {
          <li>
            <a [href]="'#tp-day-' + $index" (click)="$event.preventDefault(); jump.emit($index)">
              <span class="dot" [style.background]="color($index)" aria-hidden="true">{{ $index + 1 }}</span>
              <span class="text">
                <span class="name">{{ copy.day($index + 1) }}@if (day.title) { · {{ day.title }} }</span>
                <span class="tp-muted sub">{{ sub($index, day) }}</span>
              </span>
            </a>
          </li>
        }
      </ol>
      @if (editable()) {
        <button type="button" class="tp-btn tp-btn--block" (click)="addDay.emit()">＋ {{ copy.addDay }}</button>
      }
    </nav>
  `,
  styles: [
    `
      nav { display: grid; gap: 0.75rem; }
      ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.25rem; }
      a {
        display: flex; align-items: center; gap: 0.625rem; min-height: var(--tp-tap); padding: 0.25rem 0.5rem;
        border-radius: var(--tp-radius-sm); color: inherit; text-decoration: none;
      }
      a:hover { background: var(--tp-surface-2); }
      .dot { display: grid; place-items: center; width: 1.75rem; height: 1.75rem; border-radius: 50%; color: var(--tp-on-day); font-weight: 800; font-size: 0.875rem; }
      .dot { flex: none; }
      .text { flex: 1; min-width: 0; display: grid; }
      .name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 600; }
      .sub { font-size: 0.8125rem; }
    `,
  ],
})
export class PlannerDayRailComponent {
  readonly days = input.required<PlanDay[]>();
  readonly editable = input(false);
  readonly facts = input<PlanFacts | null>(null);
  readonly jump = output<number>();
  readonly addDay = output<void>();
  readonly copy = COPY;

  color(index: number): string {
    return dayColorVar(index);
  }

  /** "3 stops · ~17 km" */
  sub(index: number, day: PlanDay): string {
    const facts = this.facts()?.days[index];
    const stops = `${day.stops.length} ${COPY.stopWord(day.stops.length)}`;
    return facts?.meters ? `${stops} · ${kmText(facts.meters, facts.approx)}` : stops;
  }
}
