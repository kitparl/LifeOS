import { Component, OnDestroy, OnInit, effect, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { SearchService } from '../../features/search/services/search.service';
import { LucideDynamicIcon } from '@lucide/angular';
import { NAV_DESTINATIONS } from '../layout/nav-registry';
import { CommandPaletteItem } from './command-palette.models';
import { CommandPaletteService } from './command-palette.service';

@Component({
  selector: 'app-command-palette',
  standalone: true,
  imports: [FormsModule, LucideDynamicIcon],
  template: `
    @if (palette.isOpen()) {
      <div
        class="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 pt-[15vh]"
        (click)="palette.close()"
      >
        <div
          class="panel w-full max-w-lg !p-0 shadow-lg"
          role="dialog"
          aria-label="Command palette"
          (click)="$event.stopPropagation()"
        >
          <div class="title-bar rounded-none border-x-0 border-t-0">Search LifeOS</div>
          <div class="p-2 border-b border-[var(--xp-border)]">
            <input
              #searchInput
              class="input-field"
              type="text"
              placeholder="Type a command or search…"
              [ngModel]="palette.query()"
              (ngModelChange)="onQueryChange($event)"
              (keydown)="onInputKeydown($event)"
            />
          </div>
          <ul class="max-h-72 overflow-y-auto text-sm">
            @for (item of displayItems; track item.id; let i = $index) {
              <li>
                <button
                  type="button"
                  class="flex w-full items-center justify-between gap-2 px-3 py-2 text-left"
                  style="transition: background 100ms ease"
                  [style.background]="i === palette.activeIndex() ? 'var(--primary-soft)' : 'transparent'"
                  [class.opacity-50]="item.disabled"
                  [disabled]="item.disabled"
                  (click)="run(item)"
                  (mouseenter)="palette.activeIndex.set(i)"
                >
                  <span class="flex min-w-0 items-center gap-2">
                    @if (item.icon) {
                      <svg class="palette-icon" [lucideIcon]="item.icon" aria-hidden="true"></svg>
                    }
                    <span class="truncate">{{ item.label }}</span>
                  </span>
                  <span class="text-xs shrink-0" style="color: var(--text-muted)">{{ item.hint ?? item.group }}</span>
                </button>
              </li>
            } @empty {
              <li class="px-3 py-4 text-center" style="color: var(--text-muted)">No matches</li>
            }
          </ul>
        </div>
      </div>
    }
    <style>
      .palette-icon {
        width: 1rem;
        height: 1rem;
        flex-shrink: 0;
        color: var(--text-muted);
        stroke: currentColor;
      }
    </style>
  `,
})
export class CommandPaletteComponent implements OnInit, OnDestroy {
  readonly palette = inject(CommandPaletteService);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);
  private readonly searchService = inject(SearchService);

  searchItems: CommandPaletteItem[] = [];
  private searchTimer?: ReturnType<typeof setTimeout>;

  constructor() {
    effect(() => {
      if (!this.palette.isOpen()) {
        this.searchItems = [];
      }
    });
  }

  get displayItems(): CommandPaletteItem[] {
    const commands = this.palette.filteredItems();
    if (this.searchItems.length === 0) {
      return commands;
    }
    return [...commands, ...this.searchItems];
  }

  ngOnInit(): void {
    const navigationItems: CommandPaletteItem[] = NAV_DESTINATIONS.filter(d => !d.hidden).map((d) => ({
      id: d.id,
      label: d.label,
      icon: d.icon,
      group: d.category ?? 'Navigation',
      route: d.route,
    }));

    this.palette.registerItems([
      ...navigationItems,
      { id: 'settings-profile', label: 'Settings: Profile', group: 'Settings', route: '/settings#profile' },
      { id: 'settings-export', label: 'Settings: Export', group: 'Settings', route: '/settings#export' },
      { id: 'settings-sidebar', label: 'Settings: Sidebar', group: 'Settings', route: '/settings#sidebar' },
      { id: 'insights-reports', label: 'Insights: Reports', group: 'Insights', route: '/insights?tab=reports' },
      { id: 'insights-predictions', label: 'Insights: Predictions', group: 'Insights', route: '/insights?tab=predictions' },
      { id: 'analytics-overview', label: 'Analytics: Dashboard', group: 'Analytics', route: '/analytics/dashboard' },
      { id: 'analytics-productivity', label: 'Analytics: Productivity', group: 'Analytics', route: '/analytics/dashboard?tab=productivity' },
      { id: 'analytics-goals', label: 'Analytics: Goals', group: 'Analytics', route: '/analytics/dashboard?tab=goals' },
      { id: 'analytics-habits', label: 'Analytics: Habits', group: 'Analytics', route: '/analytics/dashboard?tab=habits' },
      { id: 'analytics-journal', label: 'Analytics: Journal', group: 'Analytics', route: '/analytics/dashboard?tab=journal' },
      { id: 'analytics-ai', label: 'Analytics: AI Insights', group: 'Analytics', route: '/analytics/dashboard?tab=ai' },
      { id: 'timeline-milestones', label: 'Timeline: Milestones', group: 'Timeline', route: '/timeline?tab=milestones' },
      { id: 'documents-library', label: 'Documents: Library', group: 'Documents', route: '/documents?tab=library' },
      { id: 'documents-scan', label: 'Documents: Scan / OCR', group: 'Documents', route: '/documents?tab=scan' },
      { id: 'logout', label: 'Log out', group: 'Actions', action: () => this.auth.logout().subscribe() },
      { id: 'new-habit', label: 'New Habit', group: 'Actions', route: '/habits/new' },
      { id: 'log-run', label: 'Log Run', group: 'Actions', route: '/running/new' },
      { id: 'new-event', label: 'New Event', group: 'Actions', route: '/calendar/new' },
      { id: 'new-routine', label: 'New Routine', group: 'Actions', route: '/routines/new' },
      { id: 'new-journal', label: 'New Journal', group: 'Actions', route: '/journal/new' },
      { id: 'add-word', label: 'Add Word', group: 'Actions', route: '/communication/vocabulary/new' },
      { id: 'add-qa', label: 'New Q&A', group: 'Actions', route: '/qa/new' },
      { id: 'add-wishlist', label: 'New Wishlist', group: 'Actions', route: '/wishlist/new' },
    ]);
  }

  ngOnDestroy(): void {
    clearTimeout(this.searchTimer);
  }

  onQueryChange(value: string): void {
    this.palette.setQuery(value);
    clearTimeout(this.searchTimer);
    const q = value.trim();
    if (q.length < 2) {
      this.searchItems = [];
      return;
    }
    this.searchTimer = setTimeout(() => {
      this.searchService.search(q, 8).subscribe({
        next: (res) => {
          const items: CommandPaletteItem[] = res.results.map((r) => ({
            id: `search-${r.module}-${r.id}`,
            label: r.title,
            group: 'Search',
            hint: r.subtitle ?? r.module,
            route: r.route,
          }));
          if (res.total > res.results.length) {
            items.push({
              id: 'search-all',
              label: `View all ${res.total} results`,
              group: 'Search',
              route: `/search?q=${encodeURIComponent(q)}`,
            });
          }
          this.searchItems = items;
        },
      });
    }, 300);
  }

  onInputKeydown(event: KeyboardEvent): void {
    const list = this.displayItems;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (list.length === 0) return;
      const next = (this.palette.activeIndex() + 1 + list.length) % list.length;
      this.palette.activeIndex.set(next);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (list.length === 0) return;
      const next = (this.palette.activeIndex() - 1 + list.length) % list.length;
      this.palette.activeIndex.set(next);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const item = list[this.palette.activeIndex()];
      if (item && !item.disabled) {
        this.run(item);
      }
    }
  }

  run(item: CommandPaletteItem): void {
    if (item.disabled) {
      return;
    }
    this.palette.close();
    this.searchItems = [];
    if (item.action) {
      item.action();
    } else if (item.route) {
      this.router.navigateByUrl(item.route);
    }
  }
}
