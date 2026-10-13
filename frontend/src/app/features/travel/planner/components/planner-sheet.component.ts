import { A11yModule } from '@angular/cdk/a11y';
import { Component, input, output } from '@angular/core';

let nextId = 0;

/**
 * The planner's one dialog shape: a bottom sheet on phones, a side sheet from tablet up.
 * Focus is trapped inside and returns to the opener on close; Esc and the backdrop close it.
 */
@Component({
  selector: 'app-planner-sheet',
  standalone: true,
  imports: [A11yModule],
  template: `
    @if (open()) {
      <div class="backdrop" (click)="closed.emit()" aria-hidden="true"></div>
      <section
        class="sheet"
        role="dialog"
        aria-modal="true"
        [attr.aria-labelledby]="titleId"
        cdkTrapFocus
        [cdkTrapFocusAutoCapture]="true"
        (keydown.escape)="closed.emit()"
      >
        <header>
          <h2 [id]="titleId">{{ heading() }}</h2>
          <button type="button" class="tp-btn tp-btn--quiet" aria-label="Close" (click)="closed.emit()">✕</button>
        </header>
        <div class="content"><ng-content /></div>
      </section>
    }
  `,
  styles: [
    `
      .backdrop { position: fixed; inset: 0; z-index: 40; background: rgb(28 23 20 / 0.45); }
      .sheet {
        position: fixed; z-index: 41; left: 0; right: 0; bottom: 0; max-height: 92dvh;
        display: flex; flex-direction: column; background: var(--tp-surface); color: var(--tp-text);
        border-radius: var(--tp-radius) var(--tp-radius) 0 0; box-shadow: 0 -8px 32px rgb(0 0 0 / 0.2);
        padding-bottom: env(safe-area-inset-bottom); animation: up var(--tp-ease) both;
      }
      header { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0.75rem 1rem 0.25rem; }
      h2 { font-size: var(--tp-text-xl); }
      .content { overflow-y: auto; padding: 0.5rem 1rem 1rem; }
      @media (min-width: 640px) {
        .sheet {
          left: auto; top: 0; width: min(440px, 100vw); max-height: none;
          border-radius: var(--tp-radius) 0 0 var(--tp-radius); animation-name: side;
        }
      }
      @keyframes up { from { transform: translateY(16px); opacity: 0; } }
      @keyframes side { from { transform: translateX(16px); opacity: 0; } }
    `,
  ],
})
export class PlannerSheetComponent {
  readonly open = input(false);
  readonly heading = input.required<string>();
  readonly closed = output<void>();
  readonly titleId = `tp-sheet-${++nextId}`;
}
