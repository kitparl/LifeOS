import { Component, computed, input, output, signal } from '@angular/core';
import { copyText } from '../../../../core/utils/clipboard';
import { COPY } from '../planner-copy';
import { isInAppBrowser } from '../planner-identity';
import { PlannerGoogleButtonComponent } from './google-button.component';
import { PlannerSheetComponent } from './planner-sheet.component';

/**
 * "Who are you?" on the first change: Continue with Google, or just a name. Both equally easy;
 * in-app browsers (where Google blocks sign-in) get a way out, so there is never a dead end.
 */
@Component({
  selector: 'app-planner-who',
  standalone: true,
  imports: [PlannerSheetComponent, PlannerGoogleButtonComponent],
  template: `
    <app-planner-sheet [open]="open()" [heading]="copy.whoTitle" (closed)="closed.emit()">
      <!-- Projected content is created even while the sheet is closed: only build it (and load Google) when open. -->
      @if (open()) {
      <div class="who">
        <p>{{ copy.whoIntro(ownerName()) }}</p>
        @if (error()) { <p class="error" role="alert">{{ error() }}</p> }

        @if (googleEnabled()) {
          <div class="block">
            @if (inApp() || googleFailed()) {
              <p class="hint" data-testid="who-inapp">{{ inApp() ? copy.inAppBrowser : copy.googleFailed }}</p>
              <button type="button" class="tp-btn" (click)="copyLink()">{{ copied() ? copy.linkCopied : copy.copyLink }}</button>
            }
            @if (!googleFailed()) {
              <app-planner-google-button (credential)="google.emit($event)" (failed)="googleFailed.set(true)" />
              <p class="tp-muted small">{{ copy.privacy(ownerName()) }}</p>
            }
          </div>
        }

        @if (namesAllowed()) {
          @if (googleEnabled()) { <p class="or tp-muted" aria-hidden="true">or</p> }
          <form class="block" (submit)="$event.preventDefault(); submitName()">
            <label class="tp-label" for="tp-name">{{ copy.yourName }}</label>
            <input id="tp-name" class="tp-input" data-testid="who-name" maxlength="40" autocomplete="given-name"
              [value]="name()" (input)="name.set(value($event))" />
            <button type="submit" class="tp-btn tp-btn--primary tp-btn--block" data-testid="who-continue" [disabled]="!canSubmit()">
              {{ copy.justName }}
            </button>
          </form>
        } @else {
          <p class="tp-muted">{{ copy.googleNeeded(ownerName()) }}</p>
        }
      </div>
      }
    </app-planner-sheet>
  `,
  styles: [
    `
      .who { display: grid; gap: 1rem; }
      .block { display: grid; gap: 0.5rem; }
      .hint { padding: 0.75rem; border-radius: var(--tp-radius-sm); background: var(--tp-surface-2); }
      .small { font-size: 0.875rem; text-align: center; }
      .or { text-align: center; }
      .error { color: var(--tp-danger); }
    `,
  ],
})
export class PlannerWhoComponent {
  readonly open = input(false);
  readonly ownerName = input.required<string>();
  readonly namesAllowed = input(true);
  readonly googleEnabled = input(true);
  readonly busy = input(false);
  readonly error = input<string | null>(null);
  readonly google = output<string>();
  readonly named = output<string>();
  readonly closed = output<void>();

  readonly copy = COPY;
  readonly inApp = signal(isInAppBrowser());
  readonly googleFailed = signal(false);
  readonly copied = signal(false);
  readonly name = signal('');
  readonly canSubmit = computed(() => !this.busy() && this.name().trim().length > 0);

  value(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  submitName(): void {
    if (this.canSubmit()) this.named.emit(this.name().trim());
  }

  async copyLink(): Promise<void> {
    this.copied.set(await copyText(location.href));
  }
}
