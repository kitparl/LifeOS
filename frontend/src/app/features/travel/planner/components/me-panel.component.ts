import { Component, input, output, signal } from '@angular/core';
import { ContributorMe } from '../../models/share.models';
import { COPY } from '../planner-copy';
import { PlannerGoogleButtonComponent } from './google-button.component';

/** "Me": who you are here, keeping a name-only plan safe with Google, starting over, forgetting this device. */
@Component({
  selector: 'app-planner-me',
  standalone: true,
  imports: [PlannerGoogleButtonComponent],
  template: `
    <div class="me">
      @if (contributor(); as c) {
        <p class="name">{{ c.kind === 'google' ? copy.me.signedInGoogle(c.display_name) : copy.me.signedInName(c.display_name) }}</p>
        @if (c.kind === 'name') {
          <p class="note" data-testid="me-name-note">{{ copy.nameOnlyNote }}</p>
          @if (googleEnabled() && !googleFailed()) {
            <p class="tp-label">{{ copy.keepSafe }}</p>
            <app-planner-google-button (credential)="upgrade.emit($event)" (failed)="googleFailed.set(true)" />
          }
        }
        @if (editable()) {
          <button type="button" class="tp-btn" (click)="startOver.emit()">{{ copy.me.startOver }}</button>
        }
        <button type="button" class="tp-btn tp-btn--quiet" (click)="forget.emit()">{{ copy.me.forget }}</button>
      } @else {
        <p class="tp-muted">{{ copy.me.notJoined }}</p>
      }
    </div>
  `,
  styles: [
    `
      .me { display: grid; gap: 0.75rem; }
      .name { font-size: var(--tp-text-xl); font-weight: 700; }
      .note { padding: 0.75rem; border-radius: var(--tp-radius-sm); background: var(--tp-surface-2); }
    `,
  ],
})
export class PlannerMeComponent {
  readonly contributor = input<ContributorMe | null>(null);
  readonly googleEnabled = input(true);
  readonly editable = input(false);
  readonly upgrade = output<string>();
  readonly startOver = output<void>();
  readonly forget = output<void>();
  readonly copy = COPY;
  readonly googleFailed = signal(false);
}
