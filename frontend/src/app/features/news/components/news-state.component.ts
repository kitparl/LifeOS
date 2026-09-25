import { Component, input, output } from '@angular/core';

/** Empty or error state with an optional Retry. Messages are friendly; no internal details. */
@Component({
  selector: 'app-news-state',
  standalone: true,
  template: `
    <div class="empty-state" [attr.role]="retryable() ? 'alert' : 'status'">
      <p class="empty-state__title">{{ title() }}</p>
      @if (message()) {
        <p class="empty-state__desc">{{ message() }}</p>
      }
      @if (retryable()) {
        <button type="button" class="btn-secondary" data-testid="news-state-retry-button" (click)="retry.emit()">
          Try again
        </button>
      }
    </div>
  `,
})
export class NewsStateComponent {
  readonly title = input.required<string>();
  readonly message = input<string | null>(null);
  readonly retryable = input(false);
  readonly retry = output<void>();
}
