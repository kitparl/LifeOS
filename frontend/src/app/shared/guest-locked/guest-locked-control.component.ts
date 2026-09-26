import { Component, ElementRef, HostListener, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

let nextId = 0;

/**
 * An account-only action shown to a logged-out visitor. The projected trigger (e.g. a star icon)
 * stays visible but performs nothing; clicking it opens a small popover explaining that the action
 * needs an account, with a Sign in link. Dismissed with Escape or an outside click.
 */
@Component({
  selector: 'app-guest-locked-control',
  standalone: true,
  imports: [RouterLink],
  host: {
    class: 'relative inline-block',
    '[class.z-50]': 'open()',
  },
  template: `
    <button
      type="button"
      class="btn-ghost !min-h-8 !px-2"
      style="color: var(--text-faint)"
      aria-disabled="true"
      aria-haspopup="dialog"
      [attr.aria-label]="label()"
      [attr.aria-expanded]="open()"
      [attr.aria-describedby]="open() ? popoverId : null"
      [attr.data-testid]="testId()"
      (click)="toggle()"
    >
      <ng-content />
    </button>

    @if (open()) {
      <div
        [id]="popoverId"
        class="menu absolute right-0 bottom-full z-50 mb-1 w-60 max-w-[80vw] space-y-2 p-3"
        role="dialog"
        [attr.aria-label]="message()"
      >
        <p class="text-xs font-semibold" style="color: var(--text)">{{ message() }}</p>
        @if (detail()) {
          <p class="text-xs" style="color: var(--text-muted)">{{ detail() }}</p>
        }
        <a routerLink="/login" class="btn-primary !min-h-8 w-full text-xs" [attr.data-testid]="testId() + '-sign-in-link'">
          Sign in
        </a>
      </div>
    }
  `,
})
export class GuestLockedControlComponent {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  /** Accessible name of the locked action, e.g. "Save article (sign in required)". */
  readonly label = input.required<string>();
  readonly message = input('Sign in required');
  readonly detail = input<string | null>(null);
  readonly testId = input('guest-locked-control');

  readonly open = signal(false);
  readonly popoverId = `guest-locked-popover-${nextId++}`;

  toggle(): void {
    this.open.update((v) => !v);
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (!this.open()) return;
    this.open.set(false);
    this.host.nativeElement.querySelector('button')?.focus();
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (this.open() && !this.host.nativeElement.contains(event.target as Node)) this.open.set(false);
  }
}
