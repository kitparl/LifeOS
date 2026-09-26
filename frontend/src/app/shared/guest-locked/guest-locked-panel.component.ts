import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

/** Calm empty state for an account-only section viewed by a logged-out visitor, with a Sign in link. */
@Component({
  selector: 'app-guest-locked-panel',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="empty-state" role="status" [attr.data-testid]="testId()">
      <p class="empty-state__title">{{ title() }}</p>
      @if (message()) {
        <p class="empty-state__desc">{{ message() }}</p>
      }
      <a routerLink="/login" class="btn-primary" [attr.data-testid]="testId() + '-sign-in-link'">Sign in</a>
    </div>
  `,
})
export class GuestLockedPanelComponent {
  readonly title = input('Not available for free users');
  readonly message = input<string | null>(null);
  readonly testId = input('guest-locked-panel');
}
