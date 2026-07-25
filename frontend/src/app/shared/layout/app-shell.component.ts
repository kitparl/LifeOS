import { DOCUMENT } from '@angular/common';
import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
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
import { NavPreferencesService } from '../../core/services/nav-preferences.service';
import { AssistantShellService } from '../../core/services/assistant-shell.service';
import { LucideDynamicIcon } from '@lucide/angular';
import { resolvePageTitle } from './nav-registry';

const STORAGE_AI_OPEN    = 'lifeos-ai-panel-open';
const STORAGE_COLLAPSED  = 'lifeos-sidebar-collapsed';
const STORAGE_HIDDEN     = 'lifeos-sidebar-hidden';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    CommandPaletteComponent,
    AiChatPanelComponent,
    LucideDynamicIcon,
  ],
  template: `
    <app-command-palette />

    <!-- Mobile overlays backdrop -->
    @if (drawerOpen() || assistantShell.mobileOpen()) {
      <button
        type="button"
        aria-label="Close overlay"
        class="fixed inset-0 z-40 lg:hidden"
        style="background: rgba(0,0,0,0.45)"
        (click)="closeOverlays()"
      ></button>
    }

    <!-- ====== Root: 3-column fixed layout ====== -->
    <div class="flex overflow-hidden" style="height: 100dvh; background: var(--page-bg)">

      <!-- ====== LEFT SIDEBAR (desktop only) ====== -->
      @if (!sidebarHidden()) {
      <aside
        class="hidden shrink-0 flex-col overflow-hidden lg:flex"
        style="background: var(--sidebar-bg); border-right: 1px solid var(--border);"
        [style.width]="sidebarCollapsed() ? '56px' : '220px'"
      >
        <!-- Brand header -->
        <div class="flex shrink-0 items-center justify-between"
             style="padding: 0.625rem 0.625rem 0.625rem 0.875rem; border-bottom: 1px solid var(--border); min-height: 48px;">
          @if (!sidebarCollapsed()) {
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold" style="color: var(--text)">LifeOS</p>
              <p class="text-[11px]" style="color: var(--text-faint)">Focused workspace</p>
            </div>
          }
          <button
            type="button"
            class="btn-ghost shrink-0 !px-2 !py-1 !min-h-auto text-xs"
            style="font-size: 0.7rem; color: var(--text-muted)"
            (click)="toggleSidebar()"
            [title]="sidebarCollapsed() ? 'Expand sidebar' : 'Collapse sidebar'"
          >
            {{ sidebarCollapsed() ? '›' : '‹' }}
          </button>
        </div>

        <!-- Search -->
        @if (!sidebarCollapsed()) {
          <div style="padding: 0.5rem 0.625rem 0.25rem">
            <button
              type="button"
              class="input-field text-left text-xs w-full"
              style="color: var(--text-faint); min-height: 28px"
              (click)="openSearch()"
            >
              Search… <kbd style="opacity: 0.6; font-size: 10px">⌘K</kbd>
            </button>
          </div>
        }

        <!-- Nav items -->
        <nav class="flex-1 overflow-y-auto" style="padding: 0.375rem 0.375rem; min-height: 0">
          @for (group of navGroups(); track group.category) {
            @if (!sidebarCollapsed()) {
              <p class="section-heading" style="padding: 0.5rem 0.5rem 0.25rem">{{ group.category }}</p>
            }
            @for (item of group.items; track item.id) {
              <div
                class="nav-row"
                [class.nav-row--collapsed]="sidebarCollapsed()"
                [class.nav-row--pinned]="navPrefs.isPinnedTop(item.id)"
              >
                <a
                  [routerLink]="item.route"
                  routerLinkActive="nav-item--active"
                  class="nav-item"
                  [class.nav-item--truncated]="sidebarCollapsed()"
                  [title]="sidebarCollapsed() ? item.label : ''"
                >
                  @if (item.icon) {
                    <svg class="nav-item__icon" [lucideIcon]="item.icon" aria-hidden="true"></svg>
                  }
                  @if (!sidebarCollapsed()) {
                    <span class="nav-item__label">{{ item.label }}</span>
                  }
                </a>
                @if (!sidebarCollapsed()) {
                  <button
                    type="button"
                    class="nav-pin"
                    [class.nav-pin--active]="navPrefs.isPinnedTop(item.id)"
                    [title]="navPrefs.isPinnedTop(item.id) ? 'Unpin from top' : 'Pin to top'"
                    [attr.aria-label]="navPrefs.isPinnedTop(item.id) ? 'Unpin ' + item.label + ' from top' : 'Pin ' + item.label + ' to top'"
                    (click)="onTogglePinTop($event, item.id)"
                  >
                    <svg
                      class="nav-pin__icon"
                      [lucideIcon]="navPrefs.isPinnedTop(item.id) ? 'pin' : 'pin-off'"
                      aria-hidden="true"
                    ></svg>
                  </button>
                }
              </div>
            }
          }
        </nav>

        <!-- Sidebar footer -->
        <div class="shrink-0" style="border-top: 1px solid var(--border); padding: 0.5rem 0.5rem">
          @if (!sidebarCollapsed()) {
            <button type="button" class="btn-ghost w-full text-xs justify-start" (click)="cycleTheme()">
              {{ theme.label() }}
            </button>
            @if (pwa.installAvailable()) {
              <button type="button" class="btn-primary w-full text-xs mt-1" (click)="promptInstall()">Install app</button>
            }
            @if (pwa.updateAvailable()) {
              <button type="button" class="btn-primary w-full text-xs mt-1" (click)="applyUpdate()">Update ready</button>
            }
            <button type="button" class="btn-ghost w-full text-xs justify-start mt-1" style="color: var(--text-muted)" (click)="onLogout()">
              Log out
            </button>
          } @else {
            <button type="button" class="btn-ghost w-full !px-0 text-xs" title="Log out" (click)="onLogout()">✕</button>
          }
        </div>
      </aside>
      }

      <!-- ====== CENTER COLUMN ====== -->
      <div class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">

        <!-- Sticky header bar -->
        <header class="shrink-0 flex items-center justify-between gap-2"
                style="padding: 0 1rem; min-height: 48px; background: var(--header-bg); border-bottom: 1px solid var(--border);">
          <!-- Left: Mobile menu + title -->
          <div class="flex items-center gap-2 min-w-0">
            <button type="button" class="btn-ghost !px-2 lg:hidden" (click)="toggleDrawer()">☰</button>
            <!-- Desktop sidebar toggle: matches mobile open/close behaviour -->
            <button type="button" class="btn-ghost !px-2 hidden lg:inline-flex" (click)="toggleSidebarHidden()" [title]="sidebarHidden() ? 'Show sidebar' : 'Hide sidebar'">☰</button>
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold" style="color: var(--text)">{{ currentTitle() }}</p>
            </div>
          </div>

          <!-- Right: actions -->
          <div class="flex items-center gap-1.5 shrink-0">
            @if (syncLabel(); as label) {
              <span class="hidden items-center gap-1 text-xs sm:flex" style="color: var(--text-muted)">
                <span class="inline-block h-2 w-2 rounded-full" [style.background]="syncDotColor()"></span>
                {{ label }}
              </span>
            }
            <button type="button" class="btn-ghost !px-2 text-xs hidden sm:inline-flex" (click)="openSearch()">
              Search <kbd style="font-size: 10px; opacity: 0.7; margin-left: 4px">⌘K</kbd>
            </button>
            <button type="button" class="btn-ghost !px-2 text-xs hidden sm:inline-flex" (click)="cycleTheme()" style="color: var(--text-muted)">
              {{ theme.label() }}
            </button>
            <!-- Desktop AI toggle -->
            <button
              type="button"
              class="btn-secondary text-xs hidden lg:inline-flex"
              (click)="toggleAiPanel()"
            >
              {{ aiPanelOpen() ? 'Hide Assistant' : 'Assistant' }}
            </button>
          </div>
        </header>

        <!-- PWA banner -->
        @if (pwa.installAvailable() || pwa.updateAvailable()) {
          <div class="shrink-0 flex flex-wrap items-center gap-2 text-xs"
               style="padding: 0.4rem 1rem; background: var(--surface-2); border-bottom: 1px solid var(--border)">
            @if (pwa.installAvailable()) {
              <button type="button" class="btn-primary text-xs" (click)="promptInstall()">Install app</button>
            }
            @if (pwa.updateAvailable()) {
              <button type="button" class="btn-primary text-xs" (click)="applyUpdate()">Reload update</button>
            }
          </div>
        }

        <!-- Main content + AI panel row -->
        <div class="flex flex-1 min-h-0 overflow-hidden">
          <!-- Scrollable main content (full-height routes pin their own scroll) -->
          <main
            class="flex-1 min-w-0 min-h-0"
            [class.overflow-y-auto]="!fullHeightRoute()"
            [class.overflow-hidden]="fullHeightRoute()"
            [class.flex]="fullHeightRoute()"
            [class.flex-col]="fullHeightRoute()"
            [style.padding]="fullHeightRoute() ? '0' : '1.25rem 1.5rem 5rem'"
          >
            <router-outlet />
          </main>

          <!-- Right AI panel (desktop) -->
          @if (aiPanelOpen()) {
            <aside
              class="hidden shrink-0 flex-col overflow-hidden min-h-0 lg:flex"
              style="width: 320px; border-left: 1px solid var(--border); background: var(--surface)"
            >
              <app-ai-chat-panel />
            </aside>
          }
        </div>

        <!-- Mobile bottom nav -->
        <nav class="safe-x safe-bottom shrink-0 lg:hidden"
             style="border-top: 1px solid var(--border); background: var(--sidebar-bg); padding: 0.375rem 0.5rem">
          <!-- 3 pinned + AI (always) + More = 5 columns -->
          <div class="grid gap-1" style="grid-template-columns: repeat(5, 1fr)">
            @for (item of mobileNav(); track item.id) {
              <a
                [routerLink]="item.route"
                routerLinkActive="mobile-nav--active"
                class="mobile-nav-item"
              >
                @if (item.icon) {
                  <svg class="mobile-nav-item__icon" [lucideIcon]="item.icon" aria-hidden="true"></svg>
                }
                <span>{{ item.shortLabel ?? item.label }}</span>
              </a>
            }
            <!-- Dedicated AI button — always visible, independent of pin order -->
            <button
              type="button"
              class="mobile-nav-item"
              [class.mobile-nav--active]="assistantShell.mobileOpen()"
              (click)="openMobileAi()"
            >
              <svg class="mobile-nav-item__icon" lucideIcon="sparkles" aria-hidden="true"></svg>
              <span>AI</span>
            </button>
            <button type="button" class="mobile-nav-item" (click)="toggleDrawer()">
              <svg class="mobile-nav-item__icon" lucideIcon="menu" aria-hidden="true"></svg>
              <span>More</span>
            </button>
          </div>
        </nav>
      </div>
    </div>

    <!-- ====== MOBILE DRAWER ====== -->
    <aside
      class="fixed inset-y-0 left-0 z-50 flex flex-col overflow-hidden lg:hidden"
      style="width: min(85vw, 300px); background: var(--sidebar-bg); border-right: 1px solid var(--border); box-shadow: var(--shadow-lg); transform: translateX(-100%); transition: transform 200ms ease;"
      [style.transform]="drawerOpen() ? 'translateX(0)' : 'translateX(-100%)'"
      role="dialog"
      aria-modal="true"
      aria-label="Navigation menu"
    >
      <div class="flex shrink-0 items-center justify-between"
           style="padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); min-height: 48px;">
        <p class="text-sm font-semibold" style="color: var(--text)">LifeOS</p>
        <button type="button" class="btn-ghost text-xs !px-2" (click)="closeDrawer()">✕ Close</button>
      </div>
      <div style="padding: 0.5rem 0.75rem 0.25rem">
        <button type="button" class="input-field text-left text-xs w-full" style="color: var(--text-faint); min-height: 34px" (click)="openSearch()">
          Search workspace
        </button>
      </div>
      <nav class="flex-1 overflow-y-auto" style="padding: 0.375rem 0.5rem; min-height: 0">
        @for (group of navGroups(); track group.category) {
          <p class="section-heading" style="padding: 0.5rem 0.375rem 0.25rem">{{ group.category }}</p>
          @for (item of group.items; track item.id) {
            <div
              class="nav-row"
              [class.nav-row--pinned]="navPrefs.isPinnedTop(item.id)"
            >
              @if (item.route === '/assistant') {
                <button
                  type="button"
                  class="nav-item w-full text-left"
                  [class.nav-item--active]="assistantShell.mobileOpen()"
                  (click)="openAssistantFromNav()"
                >
                  @if (item.icon) {
                    <svg class="nav-item__icon" [lucideIcon]="item.icon" aria-hidden="true"></svg>
                  }
                  <span class="nav-item__label">{{ item.label }}</span>
                </button>
              } @else {
                <a
                  [routerLink]="item.route"
                  routerLinkActive="nav-item--active"
                  class="nav-item"
                  (click)="closeDrawer()"
                >
                  @if (item.icon) {
                    <svg class="nav-item__icon" [lucideIcon]="item.icon" aria-hidden="true"></svg>
                  }
                  <span class="nav-item__label">{{ item.label }}</span>
                </a>
              }
              <button
                type="button"
                class="nav-pin"
                [class.nav-pin--active]="navPrefs.isPinnedTop(item.id)"
                [title]="navPrefs.isPinnedTop(item.id) ? 'Unpin from top' : 'Pin to top'"
                [attr.aria-label]="navPrefs.isPinnedTop(item.id) ? 'Unpin ' + item.label + ' from top' : 'Pin ' + item.label + ' to top'"
                (click)="onTogglePinTop($event, item.id)"
              >
                <svg
                  class="nav-pin__icon"
                  [lucideIcon]="navPrefs.isPinnedTop(item.id) ? 'pin' : 'pin-off'"
                  aria-hidden="true"
                ></svg>
              </button>
            </div>
          }
        }
      </nav>
      <div class="shrink-0" style="border-top: 1px solid var(--border); padding: 0.5rem 0.75rem">
        <button type="button" class="btn-ghost w-full text-xs justify-start" (click)="cycleTheme()">{{ theme.label() }}</button>
        <button type="button" class="btn-ghost w-full text-xs justify-start mt-1" style="color: var(--text-muted)" (click)="onLogout()">Log out</button>
      </div>
    </aside>

    <!-- ====== MOBILE AI BOTTOM SHEET ====== -->
    @if (assistantShell.mobileOpen()) {
      <section
        class="safe-bottom fixed inset-x-0 bottom-0 z-50 flex flex-col overflow-hidden lg:hidden"
        style="height: min(82dvh, calc(100dvh - 56px)); background: var(--surface); border: 1px solid var(--border); border-bottom: none; border-radius: 12px 12px 0 0; box-shadow: var(--shadow-lg)"
        role="dialog"
        aria-modal="true"
        aria-label="AI assistant"
      >
        <div class="shrink-0 flex items-center justify-between"
             style="padding: 0.625rem 0.875rem; border-bottom: 1px solid var(--border)">
          <p class="text-sm font-medium" style="color: var(--text)">Assistant</p>
          <button type="button" class="btn-ghost text-xs !px-2" (click)="closeMobileAi()">✕</button>
        </div>
        <div style="flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden;">
          <app-ai-chat-panel />
        </div>
      </section>
    }

    <!-- Nav item + mobile nav styles -->
    <style>
      .nav-row {
        display: flex;
        align-items: stretch;
        gap: 1px;
        margin-bottom: 1px;
        border-radius: 4px;
        position: relative;
      }
      .nav-row:hover {
        background: var(--sidebar-hover-bg);
      }
      .nav-row:hover .nav-item:not(.nav-item--active),
      .nav-row:hover .nav-pin:not(:focus-visible) {
        background: transparent;
      }
      .nav-row:has(.nav-item--active) {
        background: var(--sidebar-active-bg);
      }
      .nav-row:has(.nav-item--active):hover {
        background: var(--sidebar-active-bg);
      }
      .nav-row--collapsed {
        justify-content: center;
      }
      .nav-item {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        flex: 1;
        min-width: 0;
        padding: 0.375rem 0.5rem 0.375rem 0.625rem;
        border-radius: 4px;
        font-size: 0.8125rem;
        color: var(--text);
        text-decoration: none;
        background: transparent;
        border: none;
        cursor: pointer;
        transition: background 100ms ease, color 100ms ease;
        white-space: nowrap;
        overflow: hidden;
        font-weight: 400;
        text-align: left;
      }
      .nav-item__icon {
        flex-shrink: 0;
        width: 1rem;
        height: 1rem;
        color: inherit;
        stroke: currentColor;
      }
      .nav-pin__icon {
        width: 0.875rem;
        height: 0.875rem;
        color: inherit;
        stroke: currentColor;
      }
      .nav-item__label {
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .nav-item:hover {
        background: var(--sidebar-hover-bg);
      }
      .nav-item--active {
        background: var(--sidebar-active-bg) !important;
        color: var(--sidebar-active-text) !important;
        font-weight: 500;
      }
      .nav-row:has(.nav-item--active) .nav-item--active {
        background: transparent !important;
      }
      .nav-item--collapsed {
        justify-content: center;
        padding: 0.4rem 0;
        flex: none;
        width: 100%;
      }
      .nav-pin {
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.75rem;
        margin: 1px;
        border: none;
        border-radius: 3px;
        background: transparent;
        color: var(--text-muted);
        font-size: 0.7rem;
        line-height: 1;
        cursor: pointer;
        opacity: 0;
        transition: opacity 120ms ease, background 100ms ease, color 100ms ease;
      }
      .nav-row:hover .nav-pin,
      .nav-row:focus-within .nav-pin,
      .nav-pin--active,
      .nav-pin:focus-visible {
        opacity: 1;
      }
      .nav-pin:hover {
        background: var(--surface-3);
        color: var(--text);
      }
      .nav-pin:focus-visible {
        outline: 2px solid var(--ring);
        outline-offset: 1px;
      }
      .nav-row:has(.nav-item--active) .nav-pin {
        color: rgba(255, 255, 255, 0.85);
        opacity: 0.75;
      }
      .nav-row:has(.nav-item--active):hover .nav-pin,
      .nav-row:has(.nav-item--active) .nav-pin--active,
      .nav-row:has(.nav-item--active) .nav-pin:focus-visible {
        opacity: 1;
      }
      .nav-row:has(.nav-item--active) .nav-pin:hover {
        background: rgba(255, 255, 255, 0.18);
        color: #fff;
      }
      @media (hover: none) {
        .nav-pin {
          opacity: 0.55;
        }
        .nav-pin--active {
          opacity: 1;
        }
      }
      .mobile-nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.1rem;
        padding: 0.3rem 0.2rem;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 500;
        color: var(--text-muted);
        text-decoration: none;
        background: transparent;
        border: none;
        cursor: pointer;
        transition: background 100ms ease, color 100ms ease;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        min-width: 0;
      }
      .mobile-nav-item__icon {
        width: 1.05rem;
        height: 1.05rem;
        color: inherit;
        stroke: currentColor;
      }
      .mobile-nav-item:hover {
        background: var(--surface-3);
        color: var(--text);
      }
      .mobile-nav--active {
        background: var(--primary-soft) !important;
        color: var(--primary) !important;
        font-weight: 600;
      }
    </style>
  `,
})
export class AppShellComponent implements OnInit, OnDestroy {
  private readonly document = inject(DOCUMENT);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly palette = inject(CommandPaletteService);
  readonly navPrefs = inject(NavPreferencesService);
  readonly assistantShell = inject(AssistantShellService);
  readonly sync = inject(SyncService);
  readonly theme = inject(ThemeService);
  readonly pwa = inject(PwaService);

  readonly pinnedNav = this.navPrefs.pinnedDestinations;
  // Exclude assistant from the pinned slice — it always gets its own dedicated button
  readonly mobileNav = computed(() =>
    this.pinnedNav().filter((d) => d.id !== 'assistant').slice(0, 3),
  );

  readonly navGroups = this.navPrefs.navGroups;

  readonly aiPanelOpen = signal(this.readStorage(STORAGE_AI_OPEN, true));
  readonly drawerOpen = signal(false);
  readonly sidebarCollapsed = signal(this.readStorage(STORAGE_COLLAPSED, false));
  readonly sidebarHidden = signal(this.readStorage(STORAGE_HIDDEN, false));
  readonly currentTitle = signal('Dashboard');
  readonly fullHeightRoute = signal(false);

  ngOnInit(): void {
    this.updateRoute(this.router.url);
    this.router.events.pipe(filter((e) => e instanceof NavigationEnd)).subscribe((e) => {
      this.updateRoute((e as NavigationEnd).urlAfterRedirects);
      this.closeOverlays();
    });
  }

  ngOnDestroy(): void {
    this.document.body.style.overflow = '';
  }

  syncLabel(): string | null {
    const status = this.sync.status();
    if (status === 'offline') return 'Offline';
    const pending = this.sync.pendingCount();
    if (pending > 0) return `${pending} pending`;
    return status === 'syncing' ? 'Syncing…' : null;
  }

  syncDotColor(): string {
    const status = this.sync.status();
    if (status === 'syncing') return 'var(--warning)';
    if (status === 'offline') return 'var(--text-faint)';
    return 'var(--success)';
  }

  openSearch(): void {
    this.closeOverlays();
    this.palette.open();
  }

  toggleDrawer(): void {
    const next = !this.drawerOpen();
    this.drawerOpen.set(next);
    if (next) this.assistantShell.closeMobile();
    this.updateBodyScrollLock();
  }

  closeDrawer(): void {
    this.drawerOpen.set(false);
    this.updateBodyScrollLock();
  }

  openMobileAi(): void {
    this.drawerOpen.set(false);
    this.assistantShell.openMobile();
    this.updateBodyScrollLock();
  }

  openAssistantFromNav(): void {
    this.closeDrawer();
    this.openMobileAi();
  }

  closeMobileAi(): void {
    this.assistantShell.closeMobile();
    this.updateBodyScrollLock();
  }

  closeOverlays(): void {
    this.drawerOpen.set(false);
    this.assistantShell.closeMobile();
    this.updateBodyScrollLock();
  }

  toggleSidebar(): void {
    const next = !this.sidebarCollapsed();
    this.sidebarCollapsed.set(next);
    localStorage.setItem(STORAGE_COLLAPSED, String(next));
  }

  toggleSidebarHidden(): void {
    const next = !this.sidebarHidden();
    this.sidebarHidden.set(next);
    localStorage.setItem(STORAGE_HIDDEN, String(next));
  }

  toggleAiPanel(): void {
    const next = !this.aiPanelOpen();
    this.aiPanelOpen.set(next);
    localStorage.setItem(STORAGE_AI_OPEN, String(next));
  }

  cycleTheme(): void {
    this.theme.cyclePreference();
  }

  onTogglePinTop(event: Event, id: string): void {
    event.preventDefault();
    event.stopPropagation();
    this.navPrefs.togglePinTop(id);
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
    this.currentTitle.set(resolvePageTitle(url));
    const path = url.split('?')[0].split('#')[0];
    this.fullHeightRoute.set(path === '/assistant' || path.startsWith('/assistant/'));
  }

  private updateBodyScrollLock(): void {
    this.document.body.style.overflow =
      this.drawerOpen() || this.assistantShell.mobileOpen() ? 'hidden' : '';
  }

  private readStorage(key: string, defaultValue: boolean): boolean {
    try {
      const stored = localStorage.getItem(key);
      return stored === null ? defaultValue : stored === 'true';
    } catch {
      return defaultValue;
    }
  }
}
