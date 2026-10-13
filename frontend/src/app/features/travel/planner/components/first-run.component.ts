import { Component, output, signal } from '@angular/core';
import { COPY } from '../planner-copy';

/** Three short, skippable steps the first time someone opens a plan. */
@Component({
  selector: 'app-planner-first-run',
  standalone: true,
  template: `
    <aside class="tp-card tip" role="dialog" aria-modal="false" aria-labelledby="tp-first-run-title">
      <p class="text">
        <span class="tp-muted step">{{ step() + 1 }}/{{ steps.length }}</span>
        <strong id="tp-first-run-title">{{ steps[step()].title }}.</strong>
        {{ steps[step()].body }}
      </p>
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
      .tip {
        display: flex; flex-wrap: wrap; align-items: center; gap: 0.25rem 0.75rem; padding: 0.5rem 0.5rem 0.5rem 1rem;
        border-left: 4px solid var(--tp-accent);
      }
      .text { flex: 1 1 16rem; }
      .step { font-size: 0.875rem; margin-right: 0.25rem; }
      .actions { display: flex; gap: 0.25rem; margin-left: auto; }
    `,
  ],
})
export class PlannerFirstRunComponent {
  readonly done = output<void>();
  readonly copy = COPY;
  readonly steps = COPY.firstRun;
  readonly step = signal(0);
}
