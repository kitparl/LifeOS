import { Component, input, output } from '@angular/core';
import { PlanDay } from '../../models/share.models';
import { COPY } from '../planner-copy';
import { dayColorVar } from './day-section.component';

/** Desktop left column: every day with its colour and number; jumps to it, adds days. */
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
              <span class="name">{{ copy.day($index + 1) }}@if (day.title) { · {{ day.title }} }</span>
              <span class="tp-muted count">{{ day.stops.length }}</span>
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
      .name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 600; }
    `,
  ],
})
export class PlannerDayRailComponent {
  readonly days = input.required<PlanDay[]>();
  readonly editable = input(false);
  readonly jump = output<number>();
  readonly addDay = output<void>();
  readonly copy = COPY;

  color(index: number): string {
    return dayColorVar(index);
  }
}
