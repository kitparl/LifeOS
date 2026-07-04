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
      @if (drawerOpen() || mobileAiOpen()) {
        <button
          type="button"
          aria-label="Close overlay"
          class="fixed inset-0 z-40 bg-slate-950/45 backdrop-blur-[2px] lg:hidden"
          (click)="closeOverlays()"
        ></button>
      }

      <aside
        class="hidden shrink-0 border-r border-[var(--xp-border)] bg-[var(--surface)]/92 backdrop-blur lg:flex lg:flex-col"
        [class.w-64]="!sidebarCollapsed()"
        [class.w-20]="sidebarCollapsed()"
      >
        <div class="flex items-center justify-between border-b border-[var(--xp-border)] px-3 py-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold">{{ sidebarCollapsed() ? 'LO' : 'LifeOS' }}</p>
            @if (!sidebarCollapsed()) {
              <p class="text-[11px] text-[var(--text-muted)]">Focused workspace</p>
            }
          </div>
          <button type="button" class="input-field !min-h-9 !w-auto px-2 text-[11px]" (click)="toggleSidebar()">
            {{ sidebarCollapsed() ? '>' : '<' }}
          </button>
        </div>
        <div class="px-3 pb-2 pt-3">
          @if (!sidebarCollapsed()) {
            <button type="button" class="input-field !min-h-10 !w-full text-left text-xs" (click)="openSearch()">
              Search workspace
            </button>
          }
        </div>
        <nav class="flex-1 overflow-y-auto px-2 pb-4 text-sm">
          @for (group of navGroups; track group.label) {
            <section class="mb-3">
              @if (!sidebarCollapsed()) {
                <p class="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--text-muted)]">
                  {{ group.label }}
                </p>
              }
              <div class="flex flex-col gap-0.5">
                @for (item of group.items; track item.route) {
                  <a
                    [routerLink]="item.route"
                    routerLinkActive="bg-[var(--xp-blue)] text-white shadow-sm"
                    class="rounded-lg px-3 py-2 text-[13px] transition hover:bg-[var(--surface-3)]"
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
          <button type="button" class="input-field !min-h-10 !w-full justify-center text-xs" (click)="cycleTheme()">
            Theme: {{ theme.label() }}
          </button>
          @if (pwa.installAvailable()) {
            <button type="button" class="btn-primary w-full text-xs" (click)="promptInstall()">Install app</button>
          }
          @if (pwa.updateAvailable()) {
            <button type="button" class="btn-primary w-full text-xs" (click)="applyUpdate()">Update ready</button>
          }
          <button type="button" class="btn-primary w-full text-xs" (click)="onLogout()">Log out</button>
        </div>
      </aside>

      <aside
        class="fixed inset-y-0 left-0 z-50 flex w-[min(86vw,22rem)] -translate-x-full flex-col border-r border-[var(--xp-border)] bg-[var(--surface-2)] shadow-2xl transition-transform duration-200 lg:hidden"
        [class.translate-x-0]="drawerOpen()"
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
      >
        <div class="flex items-center justify-between border-b border-[var(--xp-border)] px-4 py-3">
          <div>
            <p class="text-sm font-semibold">LifeOS</p>
            <p class="text-xs text-[var(--text-muted)]">Compact navigation</p>
          </div>
          <button type="button" class="input-field !min-h-9 !w-auto px-3 text-xs" (click)="closeDrawer()">Close</button>
        </div>
        <div class="px-3 py-3">
          <button type="button" class="input-field !min-h-10 !w-full text-left text-xs" (click)="openSearch()">
            Search everything
          </button>
        </div>
        <nav class="flex-1 overflow-y-auto px-3 pb-4 text-sm">
          @for (group of navGroups; track group.label) {
            <section class="mb-4">
              <p class="mb-2 px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--text-muted)]">
                {{ group.label }}
              </p>
              <div class="grid grid-cols-2 gap-2">
                @for (item of group.items; track item.route) {
                  <a
                    [routerLink]="item.route"
                    routerLinkActive="bg-[var(--xp-blue)] text-white shadow-sm"
                    class="rounded-lg border border-[var(--xp-border)] bg-[var(--surface)] px-3 py-2.5 text-xs transition hover:bg-[var(--surface-3)]"
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
          <button type="button" class="input-field !min-h-10 !w-full justify-center text-xs" (click)="cycleTheme()">
            Theme: {{ theme.label() }}
          </button>
          @if (pwa.installAvailable()) {
            <button type="button" class="btn-primary w-full text-xs" (click)="promptInstall()">Install app</button>
          }
          @if (pwa.updateAvailable()) {
            <button type="button" class="btn-primary w-full text-xs" (click)="applyUpdate()">Update ready</button>
          }
          <button type="button" class="btn-primary w-full text-xs" (click)="onLogout()">Log out</button>
        </div>
      </aside>

      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-30 border-b border-[var(--xp-border)] bg-[var(--surface)]/90 backdrop-blur">
          <div class="safe-x flex items-center justify-between gap-3 px-4 py-2.5 lg:px-5">
            <div class="flex min-w-0 items-center gap-2">
              <button type="button" class="input-field !min-h-9 !w-auto px-3 text-xs lg:hidden" (click)="toggleDrawer()">
                Menu
              </button>
              <div class="min-w-0">
                <p class="truncate text-base font-semibold">{{ currentTitle() }}</p>
                <p class="hidden text-xs text-[var(--text-muted)] md:block">Minimal command center</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              @if (syncLabel(); as label) {
                <span class="hidden items-center gap-1 text-xs text-[var(--text-muted)] sm:flex">
                  <span class="inline-block h-2.5 w-2.5 rounded-full" [class]="syncDotClass()"></span>
                  {{ label }}
                </span>
              }
              <button type="button" class="input-field !min-h-9 !w-auto px-3 text-xs" (click)="openSearch()">
                Search <kbd class="hidden text-[10px] opacity-70 sm:inline">Ctrl+K</kbd>
              </button>
              <button type="button" class="input-field !min-h-9 !w-auto px-3 text-xs hidden sm:inline-flex" (click)="cycleTheme()">
                {{ theme.label() }}
              </button>
              <button
                type="button"
                class="btn-primary hidden text-xs lg:inline-flex"
                (click)="aiPanelOpen.set(!aiPanelOpen())"
              >
                {{ aiPanelOpen() ? 'Hide AI' : 'AI' }}
              </button>
              <button type="button" class="btn-primary text-xs lg:hidden" (click)="openMobileAi()">AI</button>
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
          @if (aiPanelOpen()) {
            <aside class="hidden w-88 shrink-0 border-l border-[var(--xp-border)] bg-[var(--surface)]/70 p-3 lg:block">
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
            <button type="button" class="btn-primary !min-h-10 !w-full px-2 text-[11px]" (click)="openMobileAi()">AI</button>
            <button type="button" class="input-field !min-h-10 !w-full px-2 text-[11px]" (click)="toggleDrawer()">More</button>
          </div>
        </nav>
      </div>
    </div>

    @if (mobileAiOpen()) {
      <section
        class="safe-bottom fixed inset-x-0 bottom-0 z-50 max-h-[82dvh] rounded-t-3xl border border-b-0 border-[var(--xp-border)] bg-[var(--surface)] p-3 shadow-2xl lg:hidden"
        role="dialog"
        aria-modal="true"
        aria-label="AI assistant"
      >
        <div class="mx-auto mb-3 h-1 w-10 rounded-full bg-[var(--xp-border)]"></div>
        <div class="mb-2 flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold">AI Assistant</p>
            <p class="text-xs text-[var(--text-muted)]">Ask without leaving this screen</p>
          </div>
          <button type="button" class="input-field !min-h-9 !w-auto px-3 text-xs" (click)="closeMobileAi()">Close</button>
        </div>
        <div class="h-[min(68dvh,34rem)] min-h-0">
          <app-ai-chat-panel />
        </div>
      </section>
    }
  `,
})
export class AppShellComponent implements OnInit {
  private readonly document = inject(DOCUMENT);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly palette = inject(CommandPaletteService);
  readonly sync = inject(SyncService);
  readonly theme = inject(ThemeService);
  readonly pwa = inject(PwaService);

  readonly navGroups = navGroups;
  readonly mobileNav = primaryMobileNav;
  readonly aiPanelOpen = signal(true);
  readonly mobileAiOpen = signal(false);
  readonly drawerOpen = signal(false);
  readonly sidebarCollapsed = signal(false);
  readonly currentTitle = signal('Dashboard');

  ngOnInit(): void {
    this.updateRoute(this.router.url);
    this.router.events.pipe(filter((e) => e instanceof NavigationEnd)).subscribe((e) => {
      this.updateRoute((e as NavigationEnd).urlAfterRedirects);
      this.closeOverlays();
    });
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
    this.closeOverlays();
    this.palette.open();
  }

  toggleDrawer(): void {
    const next = !this.drawerOpen();
    this.drawerOpen.set(next);
    if (next) this.mobileAiOpen.set(false);
    this.updateBodyScrollLock();
  }

  closeDrawer(): void {
    this.drawerOpen.set(false);
    this.updateBodyScrollLock();
  }

  openMobileAi(): void {
    this.drawerOpen.set(false);
    this.mobileAiOpen.set(true);
    this.updateBodyScrollLock();
  }

  closeMobileAi(): void {
    this.mobileAiOpen.set(false);
    this.updateBodyScrollLock();
  }

  closeOverlays(): void {
    this.drawerOpen.set(false);
    this.mobileAiOpen.set(false);
    this.updateBodyScrollLock();
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
    const match = [...navGroups.flatMap((group) => group.items), { label: 'Offline', route: '/offline' }].find(
      (item) => url === item.route || url.startsWith(`${item.route}/`),
    );
    this.currentTitle.set(match?.label ?? 'LifeOS');
  }

  private updateBodyScrollLock(): void {
    this.document.body.style.overflow = this.drawerOpen() || this.mobileAiOpen() ? 'hidden' : '';
  }
}
