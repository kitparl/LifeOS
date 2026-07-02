import { DOCUMENT } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import {
  NavigationEnd,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { filter } from 'rxjs';
import { PwaService } from '../../core/services/pwa.service';
import { ThemeService } from '../../core/services/theme.service';
import { AuthService } from '../../core/services/auth.service';
import { DashboardService } from '../../features/dashboard/services/dashboard.service';
import { SyncService } from '../../sync/sync.service';
import { AiChatPanelComponent } from '../../features/dashboard/widgets/ai-chat-panel.component';
import { CommandPaletteComponent } from '../command-palette/command-palette.component';
import { CommandPaletteService } from '../command-palette/command-palette.service';
import { navGroups, primaryMobileNav } from './nav-items';

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
    <div class="safe-x safe-top flex min-h-dvh bg-transparent">
      @if (drawerOpen()) {
        <button
          type="button"
          aria-label="Close navigation"
          class="fixed inset-0 z-40 bg-slate-950/55 lg:hidden"
          (click)="closeDrawer()"
        ></button>
      }

      <aside
        class="hidden shrink-0 border-r border-[var(--xp-border)] bg-[var(--xp-silver)] backdrop-blur lg:flex lg:flex-col"
        [class.w-72]="!sidebarCollapsed()"
        [class.w-24]="sidebarCollapsed()"
      >
        <div class="title-bar m-3 mb-2">{{ sidebarCollapsed() ? 'LO' : 'LifeOS' }}</div>
        <div class="flex items-center justify-between px-3 pb-2">
          @if (!sidebarCollapsed()) {
            <span class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">
              Navigation
            </span>
          }
          <button type="button" class="input-field !w-auto px-3 text-xs" (click)="toggleSidebar()">
            {{ sidebarCollapsed() ? 'Expand' : 'Collapse' }}
          </button>
        </div>
        <nav class="flex-1 overflow-y-auto px-3 pb-4 text-sm">
          @for (group of navGroups; track group.label) {
            <section class="mb-4">
              @if (!sidebarCollapsed()) {
                <p class="mb-2 px-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">
                  {{ group.label }}
                </p>
              }
              <div class="flex flex-col gap-1">
                @for (item of group.items; track item.route) {
                  <a
                    [routerLink]="item.route"
                    routerLinkActive="bg-[var(--xp-blue)] text-white shadow-sm"
                    class="rounded-xl px-3 py-2.5 transition hover:bg-white/60"
                    [class.text-center]="sidebarCollapsed()"
                  >
                    {{ sidebarCollapsed() ? (item.shortLabel ?? item.label).slice(0, 2) : item.label }}
                  </a>
                }
              </div>
            </section>
          }
        </nav>
        <div class="space-y-2 border-t border-[var(--xp-border)] p-3">
          <button type="button" class="input-field !w-full justify-center text-sm" (click)="cycleTheme()">
            Theme: {{ theme.label() }}
          </button>
          @if (pwa.installAvailable()) {
            <button type="button" class="btn-primary w-full" (click)="promptInstall()">Install app</button>
          }
          @if (pwa.updateAvailable()) {
            <button type="button" class="btn-primary w-full" (click)="applyUpdate()">Update ready</button>
          }
          <button type="button" class="btn-primary w-full" (click)="onLogout()">Log out</button>
        </div>
      </aside>

      <aside
        class="fixed inset-y-0 left-0 z-50 flex w-[min(86vw,22rem)] -translate-x-full flex-col border-r border-[var(--xp-border)] bg-[var(--surface-2)] shadow-2xl transition-transform duration-200 lg:hidden"
        [class.translate-x-0]="drawerOpen()"
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
      >
        <div class="title-bar m-3 mb-2">LifeOS</div>
        <div class="flex items-center justify-between px-3 pb-3">
          <div>
            <p class="text-sm font-semibold">{{ currentTitle() }}</p>
            <p class="text-xs text-[var(--text-muted)]">Personal AI Operating System</p>
          </div>
          <button type="button" class="input-field !w-auto px-3 text-xs" (click)="closeDrawer()">Close</button>
        </div>
        <nav class="flex-1 overflow-y-auto px-3 pb-4 text-sm">
          @for (group of navGroups; track group.label) {
            <section class="mb-4">
              <p class="mb-2 px-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--text-muted)]">
                {{ group.label }}
              </p>
              <div class="flex flex-col gap-1">
                @for (item of group.items; track item.route) {
                  <a
                    [routerLink]="item.route"
                    routerLinkActive="bg-[var(--xp-blue)] text-white shadow-sm"
                    class="rounded-xl px-3 py-3 transition hover:bg-white/60"
                    (click)="closeDrawer()"
                  >
                    {{ item.label }}
                  </a>
                }
              </div>
            </section>
          }
        </nav>
        <div class="space-y-2 border-t border-[var(--xp-border)] p-3">
          <button type="button" class="input-field !w-full justify-center text-sm" (click)="cycleTheme()">
            Theme: {{ theme.label() }}
          </button>
          @if (pwa.installAvailable()) {
            <button type="button" class="btn-primary w-full" (click)="promptInstall()">Install app</button>
          }
          @if (pwa.updateAvailable()) {
            <button type="button" class="btn-primary w-full" (click)="applyUpdate()">Update ready</button>
          }
          <button type="button" class="btn-primary w-full" (click)="onLogout()">Log out</button>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-30 border-b border-[var(--xp-border)] bg-[var(--xp-panel)] backdrop-blur">
          <div class="safe-x flex items-center justify-between gap-3 px-4 py-3">
            <div class="flex min-w-0 items-center gap-2">
              <button type="button" class="input-field !w-auto px-3 text-xs lg:hidden" (click)="toggleDrawer()">
                Menu
              </button>
              <div class="min-w-0">
                <p class="truncate text-sm font-semibold">{{ currentTitle() }}</p>
                <p class="hidden text-xs text-[var(--text-muted)] sm:block">Personal AI Operating System</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              @if (syncLabel(); as label) {
                <span class="hidden items-center gap-1 text-xs text-[var(--text-muted)] sm:flex">
                  <span class="inline-block h-2.5 w-2.5 rounded-full" [class]="syncDotClass()"></span>
                  {{ label }}
                </span>
              }
              <button type="button" class="input-field !w-auto px-3 text-xs" (click)="openSearch()">
                Search <kbd class="hidden text-[10px] opacity-70 sm:inline">Ctrl+K</kbd>
              </button>
              <button type="button" class="input-field !w-auto px-3 text-xs hidden sm:inline-flex" (click)="cycleTheme()">
                {{ theme.label() }}
              </button>
              @if (showAiPanel()) {
                <button
                  type="button"
                  class="btn-primary hidden text-xs lg:inline-flex"
                  (click)="aiPanelOpen.set(!aiPanelOpen())"
                >
                  {{ aiPanelOpen() ? 'Hide AI' : 'Show AI' }}
                </button>
              }
            </div>
          </div>
          @if (pwa.installAvailable() || pwa.updateAvailable()) {
            <div class="safe-x flex flex-wrap items-center gap-2 border-t border-[var(--xp-border)] px-4 py-2 text-xs">
              @if (pwa.installAvailable()) {
                <button type="button" class="btn-primary text-xs" (click)="promptInstall()">Install app</button>
              }
              @if (pwa.updateAvailable()) {
                <button type="button" class="btn-primary text-xs" (click)="applyUpdate()">Reload update</button>
              }
            </div>
          }
        </header>

        <div class="flex min-h-0 flex-1">
          <main class="min-w-0 flex-1 overflow-auto px-4 py-4 pb-24 lg:px-6 lg:pb-6">
            <router-outlet />
          </main>
          @if (showAiPanel() && aiPanelOpen()) {
            <aside class="hidden w-80 shrink-0 border-l border-[var(--xp-border)] p-4 lg:block">
              <app-ai-chat-panel />
            </aside>
          }
        </div>

        <nav class="safe-x safe-bottom fixed inset-x-0 bottom-0 z-30 border-t border-[var(--xp-border)] bg-[var(--xp-panel)] px-2 py-2 backdrop-blur lg:hidden">
          <div class="grid grid-cols-5 gap-2">
            @for (item of mobileNav; track item.route) {
              <a
                [routerLink]="item.route"
                routerLinkActive="bg-[var(--xp-blue)] text-white"
                class="rounded-xl px-2 py-2 text-center text-[11px] font-medium"
              >
                {{ item.shortLabel ?? item.label }}
              </a>
            }
            <button type="button" class="input-field !w-full px-2 text-[11px]" (click)="toggleDrawer()">More</button>
          </div>
        </nav>
      </div>
    </div>
  `,
})
export class AppShellComponent implements OnInit {
  private readonly document = inject(DOCUMENT);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly palette = inject(CommandPaletteService);
  private readonly dashboard = inject(DashboardService);
  readonly sync = inject(SyncService);
  readonly theme = inject(ThemeService);
  readonly pwa = inject(PwaService);

  readonly navGroups = navGroups;
  readonly mobileNav = primaryMobileNav;
  readonly aiPanelOpen = signal(true);
  readonly drawerOpen = signal(false);
  readonly sidebarCollapsed = signal(false);
  readonly showAiPanel = signal(false);
  readonly currentTitle = signal('Dashboard');

  ngOnInit(): void {
    this.updateRoute(this.router.url);
    this.router.events.pipe(filter((e) => e instanceof NavigationEnd)).subscribe((e) => {
      this.updateRoute((e as NavigationEnd).urlAfterRedirects);
      this.closeDrawer();
      if (this.showAiPanel()) {
        this.dashboard.getSummary().subscribe();
      }
    });
    this.dashboard.getSummary().subscribe();
  }

  syncLabel(): string | null {
    const status = this.sync.status();
    if (status === 'offline') return 'Offline';
    const pending = this.sync.pendingCount();
    if (pending > 0) return `${pending} pending`;
    return status === 'syncing' ? 'Syncing' : 'Synced';
  }

  syncDotClass(): string {
    const status = this.sync.status();
    if (status === 'syncing') return 'bg-orange-500';
    if (status === 'offline') return 'bg-gray-500';
    return 'bg-green-600';
  }

  openSearch(): void {
    this.palette.open();
  }

  toggleDrawer(): void {
    const next = !this.drawerOpen();
    this.drawerOpen.set(next);
    this.document.body.style.overflow = next ? 'hidden' : '';
  }

  closeDrawer(): void {
    this.drawerOpen.set(false);
    this.document.body.style.overflow = '';
  }

  toggleSidebar(): void {
    this.sidebarCollapsed.set(!this.sidebarCollapsed());
  }

  cycleTheme(): void {
    this.theme.cyclePreference();
  }

  promptInstall(): void {
    void this.pwa.promptInstall();
  }

  applyUpdate(): void {
    void this.pwa.applyUpdate();
  }

  onLogout(): void {
    this.auth.logout().subscribe();
  }

  private updateRoute(url: string): void {
    this.showAiPanel.set(url.startsWith('/dashboard'));
    const match = [...navGroups.flatMap((group) => group.items), { label: 'Offline', route: '/offline' }].find(
      (item) => url === item.route || url.startsWith(`${item.route}/`),
    );
    this.currentTitle.set(match?.label ?? 'LifeOS');
  }
}
