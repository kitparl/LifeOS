import { Component, output, signal } from '@angular/core';
import { COPY } from '../planner-copy';

/** Three short, skippable steps the first time someone opens a plan. */
@Component({
  selector: 'app-planner-first-run',
  standalone: true,
  template: `
    <aside class="tp-card tip" role="dialog" aria-modal="false" aria-labelledby="tp-first-run-title">
      <p class="tp-muted step">{{ step() + 1 }} / {{ steps.length }}</p>
      <h2 id="tp-first-run-title">{{ steps[step()].title }}</h2>
      <p>{{ steps[step()].body }}</p>
      <div class="actions">
        <button type="button" class="tp-btn tp-btn--quiet" (click)="done.emit()">{{ copy.skip }}</button>
        @if (step() < steps.length - 1) {
          <button type="button" class="tp-btn tp-btn--primary" (click)="step.set(step() + 1)">{{ copy.next }}</button>
        } @else {
          <button type="button" class="tp-btn tp-btn--primary" (click)="done.emit()">{{ copy.gotIt }}</button>
        }
      </div>
    </aside>
  `,
  styles: [
    `
      .tip { display: grid; gap: 0.5rem; padding: 1rem; border-width: 2px; border-color: var(--tp-accent); }
      h2 { font-size: var(--tp-text-lg); }
      .step { font-size: 0.875rem; }
      .actions { display: flex; justify-content: flex-end; gap: 0.5rem; }
    `,
  ],
})
export class PlannerFirstRunComponent {
  readonly done = output<void>();
  readonly copy = COPY;
  readonly steps = COPY.firstRun;
  readonly step = signal(0);
}
