import { Component, effect, input, output } from '@angular/core';
import { COPY } from '../planner-copy';

const VISIBLE_MS = 7000;

/** "Removed X · Undo": deleting never loses a friend's work. Announced politely to screen readers. */
@Component({
  selector: 'app-planner-toast',
  standalone: true,
  template: `
    <div class="region" aria-live="polite">
      @if (message()) {
        <div class="toast" role="status">
          <span>{{ message() }}</span>
          @if (canUndo()) {
            <button type="button" class="tp-btn tp-btn--quiet undo" data-testid="toast-undo" (click)="undo.emit()">{{ copy.undo }}</button>
          }
        </div>
      }
    </div>
  `,
  styles: [
    `
      .region { position: fixed; left: 0; right: 0; bottom: calc(9rem + env(safe-area-inset-bottom)); z-index: 30; display: flex; justify-content: center; pointer-events: none; padding: 0 1rem; }
      .toast {
        pointer-events: auto; display: flex; align-items: center; gap: 0.75rem; max-width: 30rem;
        padding: 0.25rem 0.25rem 0.25rem 1rem; border-radius: 999px; background: var(--tp-text); color: var(--tp-bg);
        box-shadow: 0 6px 20px rgb(0 0 0 / 0.25);
      }
      .undo { color: inherit; text-decoration: underline; }
      @media (min-width: 640px) { .region { bottom: 6rem; } }
    `,
  ],
})
export class PlannerToastComponent {
  readonly message = input<string | null>(null);
  readonly canUndo = input(false);
  readonly undo = output<void>();
  readonly dismissed = output<void>();
  readonly copy = COPY;

  constructor() {
    effect((onCleanup) => {
      if (!this.message()) return;
      const timer = setTimeout(() => this.dismissed.emit(), VISIBLE_MS);
      onCleanup(() => clearTimeout(timer));
    });
  }
}
