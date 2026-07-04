import { Injectable, signal } from '@angular/core';

/** Shared mobile assistant panel state (opened from nav, routes, etc.) */
@Injectable({ providedIn: 'root' })
export class AssistantShellService {
  readonly mobileOpen = signal(false);

  openMobile(): void {
    this.mobileOpen.set(true);
  }

  closeMobile(): void {
    this.mobileOpen.set(false);
  }

  toggleMobile(): void {
    this.mobileOpen.update((open) => !open);
  }
}
