import { Component, OnInit, inject, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { DashboardService } from '../../features/dashboard/services/dashboard.service';
import { AiChatPanelComponent } from '../../features/dashboard/widgets/ai-chat-panel.component';
import { CommandPaletteComponent } from '../command-palette/command-palette.component';
import { CommandPaletteService } from '../command-palette/command-palette.service';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    CommandPaletteComponent,
    AiChatPanelComponent,
  ],
  template: `
    <app-command-palette />
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
            routerLink="/goals"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Goals</a
          >
          <a
            routerLink="/tasks"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Tasks</a
          >
          <a
            routerLink="/habits"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Habits</a
          >
          <a
            routerLink="/running"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Running</a
          >
          <a
            routerLink="/calendar"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Calendar</a
          >
          <a
            routerLink="/journal"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Journal</a
          >
          <a
            routerLink="/mood"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Mood</a
          >
          <a
            routerLink="/communication"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Communication</a
          >
          <a
            routerLink="/qa"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Q&A</a
          >
          <a
            routerLink="/wishlist"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Wishlist</a
          >
          <a
            routerLink="/notifications"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Notifications</a
          >
          <a
            routerLink="/export"
            routerLinkActive="bg-[var(--xp-blue)] text-white"
            class="rounded px-3 py-2 hover:bg-white/60"
            >Export</a
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

      <div class="flex min-w-0 flex-1 flex-col">
        <header
          class="flex items-center justify-between gap-3 border-b border-[var(--xp-border)] bg-[var(--xp-panel)] px-4 py-2"
        >
          <span class="text-sm font-semibold">Personal AI Operating System</span>
          <div class="flex items-center gap-2">
            @if (syncLabel(); as label) {
              <span class="flex items-center gap-1 text-xs text-gray-700">
                <span class="inline-block h-2 w-2 rounded-full" [class]="syncDotClass()"></span>
                {{ label }}
              </span>
            }
            <button type="button" class="input-field !w-auto text-xs py-1" (click)="openSearch()">
              Search… <kbd class="ml-1 text-[10px] opacity-70">Ctrl+K</kbd>
            </button>
            @if (showAiPanel()) {
              <button
                type="button"
                class="btn-primary text-xs hidden lg:inline-flex"
                (click)="aiPanelOpen.set(!aiPanelOpen())"
              >
                {{ aiPanelOpen() ? 'Hide AI' : 'Show AI' }}
              </button>
            }
          </div>
        </header>

        <div class="flex min-h-0 flex-1">
          <main class="min-w-0 flex-1 overflow-auto p-4">
            <router-outlet />
          </main>
          @if (showAiPanel() && aiPanelOpen()) {
            <aside class="hidden w-72 shrink-0 border-l border-[var(--xp-border)] p-3 lg:block">
              <app-ai-chat-panel />
            </aside>
          }
        </div>
      </div>
    </div>
  `,
})
export class AppShellComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly palette = inject(CommandPaletteService);
  private readonly dashboard = inject(DashboardService);

  readonly aiPanelOpen = signal(true);
  readonly showAiPanel = signal(false);

  ngOnInit(): void {
    this.updateRoute(this.router.url);
    this.router.events.pipe(filter((e) => e instanceof NavigationEnd)).subscribe((e) => {
      this.updateRoute((e as NavigationEnd).urlAfterRedirects);
      if (this.showAiPanel()) {
        this.dashboard.getSummary().subscribe();
      }
    });
    this.dashboard.getSummary().subscribe();
  }

  syncLabel(): string | null {
    const s = this.dashboard.summary();
    if (!s) {
      return null;
    }
    if (s.pending_sync_count > 0) {
      return `${s.pending_sync_count} pending`;
    }
    return s.sync_status === 'synced' ? 'Synced' : s.sync_status;
  }

  syncDotClass(): string {
    const status = this.dashboard.summary()?.sync_status ?? 'synced';
    if (status === 'syncing') return 'bg-orange-500';
    if (status === 'offline') return 'bg-gray-500';
    return 'bg-green-600';
  }

  openSearch(): void {
    this.palette.open();
  }

  onLogout(): void {
    this.auth.logout().subscribe();
  }

  private updateRoute(url: string): void {
    this.showAiPanel.set(url.startsWith('/dashboard'));
  }
}
