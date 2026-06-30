import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="flex min-h-screen">
      <aside class="w-56 shrink-0 border-r border-[var(--xp-border)] bg-[var(--xp-silver)]">
        <div class="title-bar rounded-none border-x-0 border-t-0">LifeOS</div>
        <nav class="flex flex-col gap-1 p-3 text-sm">
          <a
            routerLink="/dashboard"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Dashboard</a
          >
          <a
            routerLink="/profile"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Profile</a
          >
          <button type="button" class="btn-primary mt-4 w-full" (click)="onLogout()">
            Log out
          </button>
        </nav>
      </aside>
      <main class="flex-1 p-6">
        <router-outlet />
      </main>
    </div>
  `,
})
export class AppShellComponent {
  private readonly auth = inject(AuthService);

  onLogout(): void {
    this.auth.logout().subscribe();
  }
}
