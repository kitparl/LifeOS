import { Component, computed, input, output, signal } from '@angular/core';
import { MyPlan } from '../../models/share.models';
import { COPY } from '../planner-copy';
import { PlannerSheetComponent } from './planner-sheet.component';

/** "Send to <owner>": a sticky bar on phones, with an optional short note. */
@Component({
  selector: 'app-planner-send',
  standalone: true,
  imports: [PlannerSheetComponent],
  template: `
    <div class="bar">
      @if (plan()?.status === 'submitted') {
        <p class="status" role="status">
          ✓ {{ copy.sentBadge }}@if (plan()?.edited_since_sent) { · {{ copy.changedSinceSent }} }
        </p>
      }
      <button type="button" class="tp-btn tp-btn--primary send" data-testid="send-open" [disabled]="busy()" (click)="sheetOpen.set(true)">
        {{ label() }}
      </button>
    </div>
    <app-planner-sheet [open]="sheetOpen()" [heading]="copy.sendTitle(ownerName())" (closed)="sheetOpen.set(false)">
      <form class="form" (submit)="$event.preventDefault(); submit()">
        <label class="tp-label" for="tp-message">{{ copy.messageLabel(ownerName()) }}</label>
        <textarea id="tp-message" class="tp-input" rows="3" maxlength="500" [value]="message()" (input)="message.set(value($event))"></textarea>
        <button type="submit" class="tp-btn tp-btn--primary tp-btn--block" data-testid="send-confirm" [disabled]="busy()">{{ copy.send }}</button>
      </form>
    </app-planner-sheet>
  `,
  styles: [
    `
      .bar { display: flex; align-items: center; justify-content: flex-end; gap: 0.75rem; flex-wrap: wrap; }
      .status { color: var(--tp-ok); font-weight: 600; }
      .send { min-height: 3.25rem; padding-inline: 1.5rem; font-size: var(--tp-text-lg); }
      .form { display: grid; gap: 0.75rem; }
      @media (max-width: 639px) { .send { flex: 1; } }
    `,
  ],
})
export class PlannerSendComponent {
  readonly ownerName = input.required<string>();
  readonly plan = input<MyPlan | null>(null);
  readonly busy = input(false);
  readonly sent = output<string | null>();

  readonly copy = COPY;
  readonly sheetOpen = signal(false);
  readonly message = signal('');
  readonly label = computed(() =>
    this.plan()?.status === 'submitted' ? COPY.sendAgain(this.ownerName()) : COPY.sendTo(this.ownerName()),
  );

  value(event: Event): string {
    return (event.target as HTMLTextAreaElement).value;
  }

  submit(): void {
    this.sent.emit(this.message().trim() || null);
    this.sheetOpen.set(false);
  }
}
