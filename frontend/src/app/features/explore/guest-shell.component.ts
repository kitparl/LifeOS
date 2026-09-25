import { DOCUMENT } from '@angular/common';
import { Component, DestroyRef, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { filter } from 'rxjs';
import { ThemeService } from '../../core/services/theme.service';
import {
  EXPLORE_BASE,
  EXPLORE_HOME_TITLE,
  EXPLORE_TOOLS,
  exploreToolRoute,
  resolveExploreTitle,
} from './explore-tools.registry';

const STORAGE_COLLAPSED = 'lifeos-guest-sidebar-collapsed';
const STORAGE_HIDDEN    = 'lifeos-guest-sidebar-hidden';
const MOBILE_TOOL_SLOTS = 3;

/**
 * Public shell for Explore Tools. Mirrors AppShellComponent's layout (sidebar, header, drawer,
 * bottom nav) but intentionally has no AI, notifications, sync, word of the day, command palette,
 * pinning, or logout — it only knows about the EXPLORE_TOOLS registry.
 */
@Component({
  selector: 'app-guest-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, LucideDynamicIcon],
  styleUrl: '../../shared/layout/shell-nav.css',
  template: `
    <!-- Mobile drawer backdrop -->
    @if (drawerOpen()) {
      <button
        type="button"
        aria-label="Close overlay"
        class="fixed inset-0 z-40 lg:hidden"
        style="background: rgba(0,0,0,0.45)"
        (click)="closeDrawer()"
      ></button>
    }

    <div class="flex overflow-hidden" style="height: 100dvh; background: var(--page-bg)">

      <!-- ====== LEFT SIDEBAR (desktop only) ====== -->
      @if (!sidebarHidden()) {
      <aside
        class="hidden shrink-0 flex-col overflow-hidden lg:flex"
        style="background: var(--sidebar-bg); border-right: 1px solid var(--border);"
        [style.width]="sidebarCollapsed() ? '56px' : '220px'"
      >
        <div class="flex shrink-0 items-center justify-between"
             style="padding: 0.625rem 0.625rem 0.625rem 0.875rem; border-bottom: 1px solid var(--border); min-height: 48px;">
          @if (!sidebarCollapsed()) {
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold" style="color: var(--text)">LifeOS</p>
              <p class="text-[11px]" style="color: var(--text-faint)">Free tools</p>
            </div>
          }
          <button
            type="button"
            class="btn-ghost shrink-0 !px-2 !py-1 !min-h-auto text-xs"
            style="font-size: 0.7rem; color: var(--text-muted)"
            (click)="toggleSidebar()"
            [title]="sidebarCollapsed() ? 'Expand sidebar' : 'Collapse sidebar'"
            data-testid="guest-shell-collapse-button"
          >
            {{ sidebarCollapsed() ? '›' : '‹' }}
          </button>
        </div>

        <nav class="flex-1 overflow-y-auto" style="padding: 0.375rem 0.375rem; min-height: 0">
          @if (!sidebarCollapsed()) {
            <p class="section-heading" style="padding: 0.5rem 0.5rem 0.25rem">{{ homeTitle }}</p>
          }
          <div class="nav-row" [class.nav-row--collapsed]="sidebarCollapsed()">
            <a
              [routerLink]="homeRoute"
              routerLinkActive="nav-item--active"
              [routerLinkActiveOptions]="{ exact: true }"
              class="nav-item"
              [title]="sidebarCollapsed() ? homeTitle : ''"
              data-testid="guest-shell-nav-home"
            >
              <svg class="nav-item__icon" lucideIcon="layout-dashboard" aria-hidden="true"></svg>
              @if (!sidebarCollapsed()) {
                <span class="nav-item__label">All tools</span>
              }
            </a>
          </div>
          @for (tool of tools; track tool.id) {
            <div class="nav-row" [class.nav-row--collapsed]="sidebarCollapsed()">
              <a
                [routerLink]="routeFor(tool)"
                routerLinkActive="nav-item--active"
                class="nav-item"
                [title]="sidebarCollapsed() ? tool.label : ''"
                [attr.data-testid]="'guest-shell-nav-' + tool.id"
              >
                <svg class="nav-item__icon" [lucideIcon]="tool.icon" aria-hidden="true"></svg>
                @if (!sidebarCollapsed()) {
                  <span class="nav-item__label">{{ tool.label }}</span>
                }
              </a>
            </div>
          }
        </nav>

        <div class="shrink-0" style="border-top: 1px solid var(--border); padding: 0.5rem 0.5rem">
          @if (!sidebarCollapsed()) {
            <button type="button" class="btn-ghost w-full text-xs justify-start" (click)="cycleTheme()">
              {{ theme.label() }}
            </button>
            <a routerLink="/login" class="btn-primary w-full text-xs mt-1" data-testid="guest-shell-sidebar-sign-in">Sign in</a>
          } @else {
            <a routerLink="/login" class="btn-ghost w-full !px-0 text-xs" title="Sign in" aria-label="Sign in">
              <svg class="nav-item__icon" lucideIcon="log-in" aria-hidden="true"></svg>
            </a>
          }
        </div>
      </aside>
      }

      <!-- ====== CENTER COLUMN ====== -->
      <div class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">

        <header class="shrink-0 flex items-center justify-between gap-2"
                style="padding: 0 1rem; min-height: 48px; background: var(--header-bg); border-bottom: 1px solid var(--border);">
          <div class="flex items-center gap-2 min-w-0">
            <button
              type="button"
              class="btn-ghost !px-2"
              (click)="toggleSidebarMenu()"
              [title]="sidebarMenuTitle()"
              data-testid="guest-shell-menu-button"
            >
              ☰
            </button>
            <div class="min-w-0">
              <h1 class="truncate text-sm font-semibold" style="color: var(--text); margin: 0">{{ currentTitle() }}</h1>
            </div>
          </div>

          <div class="flex items-center gap-1.5 shrink-0">
            <button type="button" class="btn-ghost !px-2 text-xs !hidden sm:!inline-flex" (click)="cycleTheme()" style="color: var(--text-muted)">
              {{ theme.label() }}
            </button>
            <a routerLink="/login" class="btn-secondary text-xs" data-testid="guest-shell-header-sign-in">Sign in</a>
          </div>
        </header>

        <div class="flex flex-1 min-h-0 overflow-hidden">
          <main class="flex-1 min-w-0 min-h-0 overflow-y-auto" style="padding: 0.75rem 1.5rem 5rem">
            <router-outlet />
          </main>
        </div>

        <!-- Mobile bottom nav: registry tools + Sign in + More -->
        <nav class="safe-x safe-bottom shrink-0 lg:hidden"
             style="border-top: 1px solid var(--border); background: var(--sidebar-bg); padding: 0.375rem 0.5rem">
          <div class="grid gap-1" [style.grid-template-columns]="'repeat(' + (mobileTools.length + 2) + ', 1fr)'">
            @for (tool of mobileTools; track tool.id) {
              <a
                [routerLink]="routeFor(tool)"
                routerLinkActive="mobile-nav--active"
                class="mobile-nav-item"
                [attr.data-testid]="'guest-shell-mobile-nav-' + tool.id"
              >
                <svg class="mobile-nav-item__icon" [lucideIcon]="tool.icon" aria-hidden="true"></svg>
                <span>{{ tool.shortLabel ?? tool.label }}</span>
              </a>
            }
            <a routerLink="/login" class="mobile-nav-item" data-testid="guest-shell-mobile-sign-in">
              <svg class="mobile-nav-item__icon" lucideIcon="log-in" aria-hidden="true"></svg>
              <span>Sign in</span>
            </a>
            <button type="button" class="mobile-nav-item" (click)="toggleDrawer()" data-testid="guest-shell-mobile-more">
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
      <nav class="flex-1 overflow-y-auto" style="padding: 0.375rem 0.5rem; min-height: 0">
        <p class="section-heading" style="padding: 0.5rem 0.375rem 0.25rem">{{ homeTitle }}</p>
        <div class="nav-row">
          <a
            [routerLink]="homeRoute"
            routerLinkActive="nav-item--active"
            [routerLinkActiveOptions]="{ exact: true }"
            class="nav-item"
            (click)="closeDrawer()"
          >
            <svg class="nav-item__icon" lucideIcon="layout-dashboard" aria-hidden="true"></svg>
            <span class="nav-item__label">All tools</span>
          </a>
        </div>
        @for (tool of tools; track tool.id) {
          <div class="nav-row">
            <a
              [routerLink]="routeFor(tool)"
              routerLinkActive="nav-item--active"
              class="nav-item"
              (click)="closeDrawer()"
            >
              <svg class="nav-item__icon" [lucideIcon]="tool.icon" aria-hidden="true"></svg>
              <span class="nav-item__label">{{ tool.label }}</span>
            </a>
          </div>
        }
      </nav>
      <div class="shrink-0" style="border-top: 1px solid var(--border); padding: 0.5rem 0.75rem">
        <button type="button" class="btn-ghost w-full text-xs justify-start" (click)="cycleTheme()">{{ theme.label() }}</button>
        <a routerLink="/login" class="btn-primary w-full text-xs mt-1" (click)="closeDrawer()">Sign in</a>
      </div>
    </aside>
  `,
})
export class GuestShellComponent implements OnInit, OnDestroy {
  private readonly document = inject(DOCUMENT);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  readonly theme = inject(ThemeService);

  readonly tools = EXPLORE_TOOLS;
  readonly mobileTools = EXPLORE_TOOLS.slice(0, MOBILE_TOOL_SLOTS);
  readonly homeRoute = EXPLORE_BASE;
  readonly homeTitle = EXPLORE_HOME_TITLE;
  readonly routeFor = exploreToolRoute;

  readonly drawerOpen = signal(false);
  readonly sidebarCollapsed = signal(this.readStorage(STORAGE_COLLAPSED));
  readonly sidebarHidden = signal(this.readStorage(STORAGE_HIDDEN));
  readonly currentTitle = signal(EXPLORE_HOME_TITLE);
  readonly desktopLayout = signal(
    typeof window !== 'undefined' ? window.matchMedia('(min-width: 1024px)').matches : true,
  );

  private readonly desktopMediaQuery =
    typeof window !== 'undefined' ? window.matchMedia('(min-width: 1024px)') : null;
  private readonly onDesktopLayoutChange = (): void => {
    this.desktopLayout.set(this.desktopMediaQuery?.matches ?? true);
  };

  ngOnInit(): void {
    this.currentTitle.set(resolveExploreTitle(this.router.url));
    this.desktopMediaQuery?.addEventListener('change', this.onDesktopLayoutChange);
    this.router.events
      .pipe(filter((e) => e instanceof NavigationEnd), takeUntilDestroyed(this.destroyRef))
      .subscribe((e) => {
        this.currentTitle.set(resolveExploreTitle((e as NavigationEnd).urlAfterRedirects));
        this.closeDrawer();
      });
  }

  ngOnDestroy(): void {
    this.desktopMediaQuery?.removeEventListener('change', this.onDesktopLayoutChange);
    this.document.body.style.overflow = '';
  }

  toggleSidebarMenu(): void {
    if (this.desktopLayout()) {
      this.toggleSidebarHidden();
    } else {
      this.toggleDrawer();
    }
  }

  sidebarMenuTitle(): string {
    if (this.desktopLayout()) {
      return this.sidebarHidden() ? 'Show sidebar' : 'Hide sidebar';
    }
    return this.drawerOpen() ? 'Close menu' : 'Open menu';
  }

  toggleDrawer(): void {
    this.drawerOpen.set(!this.drawerOpen());
    this.updateBodyScrollLock();
  }

  closeDrawer(): void {
    this.drawerOpen.set(false);
    this.updateBodyScrollLock();
  }

  toggleSidebar(): void {
    const next = !this.sidebarCollapsed();
    this.sidebarCollapsed.set(next);
    this.writeStorage(STORAGE_COLLAPSED, next);
  }

  toggleSidebarHidden(): void {
    const next = !this.sidebarHidden();
    this.sidebarHidden.set(next);
    this.writeStorage(STORAGE_HIDDEN, next);
  }

  cycleTheme(): void {
    this.theme.cyclePreference();
  }

  private updateBodyScrollLock(): void {
    this.document.body.style.overflow = this.drawerOpen() ? 'hidden' : '';
  }

  private readStorage(key: string): boolean {
    try {
      return localStorage.getItem(key) === 'true';
    } catch {
      return false;
    }
  }

  private writeStorage(key: string, value: boolean): void {
    try {
      localStorage.setItem(key, String(value));
    } catch {
      // Storage unavailable (private mode); the in-memory signal still applies for this session.
    }
  }
}
