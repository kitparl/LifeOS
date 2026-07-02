import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-offline-page',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="safe-top safe-bottom safe-x flex min-h-dvh items-center justify-center px-4 py-10">
      <div class="panel max-w-md text-center">
        <div
          class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full border border-[var(--xp-border)] bg-[var(--xp-silver)] text-lg font-semibold text-[var(--xp-blue)]"
        >
          Off
        </div>
        <h1 class="text-xl font-semibold">You are offline</h1>
        <p class="mt-2 text-sm text-gray-600">
          LifeOS is still available for cached content, but this page needs a connection to load fresh
          data.
        </p>
        <div class="mt-5 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <button type="button" class="btn-primary" (click)="reload()">Try again</button>
          <a routerLink="/dashboard" class="input-field inline-flex !w-auto items-center justify-center no-underline">
            Back to dashboard
          </a>
        </div>
      </div>
    </div>
  `,
})
export class OfflinePageComponent {
  reload(): void {
    window.location.reload();
  }
}
