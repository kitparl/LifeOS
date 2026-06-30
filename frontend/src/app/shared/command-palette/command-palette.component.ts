import { Component, OnDestroy, OnInit, effect, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { SearchService } from '../../features/search/services/search.service';
import { CommandPaletteItem } from './command-palette.models';
import { CommandPaletteService } from './command-palette.service';

@Component({
  selector: 'app-command-palette',
  standalone: true,
  imports: [FormsModule],
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
                  class="flex w-full items-center justify-between gap-2 px-3 py-2 text-left hover:bg-[#d6e4f7]"
                  [class.bg-[#d6e4f7]]="i === palette.activeIndex()"
                  [class.opacity-50]="item.disabled"
                  [disabled]="item.disabled"
                  (click)="run(item)"
                  (mouseenter)="palette.activeIndex.set(i)"
                >
                  <span>{{ item.label }}</span>
                  <span class="text-xs text-gray-500">{{ item.hint ?? item.group }}</span>
                </button>
              </li>
            } @empty {
              <li class="px-3 py-4 text-center text-gray-500">No matches</li>
            }
          </ul>
        </div>
      </div>
    }
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
    this.palette.registerItems([
      { id: 'dashboard', label: 'Go to Dashboard', group: 'Navigation', route: '/dashboard' },
      { id: 'profile', label: 'Go to Profile', group: 'Navigation', route: '/profile' },
      { id: 'logout', label: 'Log out', group: 'Actions', action: () => this.auth.logout().subscribe() },
      { id: 'goals', label: 'Goals', group: 'Modules', route: '/goals' },
      { id: 'tasks', label: 'Tasks', group: 'Modules', route: '/tasks' },
      { id: 'habits', label: 'Habits', group: 'Modules', route: '/habits' },
      { id: 'new-habit', label: 'New Habit', group: 'Actions', route: '/habits/new' },
      { id: 'running', label: 'Running', group: 'Modules', route: '/running' },
      { id: 'log-run', label: 'Log Run', group: 'Actions', route: '/running/new' },
      { id: 'calendar', label: 'Calendar', group: 'Modules', route: '/calendar' },
      { id: 'journal', label: 'Journal', group: 'Modules', route: '/journal' },
      { id: 'mood', label: 'Mood', group: 'Modules', route: '/mood' },
      { id: 'new-event', label: 'New Event', group: 'Actions', route: '/calendar/new' },
      { id: 'new-journal', label: 'New Journal', group: 'Actions', route: '/journal/new' },
      { id: 'communication', label: 'Communication', group: 'Modules', route: '/communication' },
      { id: 'qa', label: 'Personal Q&A', group: 'Modules', route: '/qa' },
      { id: 'wishlist', label: 'Wishlist', group: 'Modules', route: '/wishlist' },
      { id: 'add-word', label: 'Add Word', group: 'Actions', route: '/communication/vocabulary/new' },
      { id: 'add-qa', label: 'New Q&A', group: 'Actions', route: '/qa/new' },
      { id: 'add-wishlist', label: 'New Wishlist', group: 'Actions', route: '/wishlist/new' },
      { id: 'search-page', label: 'Search', group: 'Tools', route: '/search' },
      { id: 'notifications', label: 'Notifications', group: 'Tools', route: '/notifications' },
      { id: 'export', label: 'Export Data', group: 'Tools', route: '/export' },
      { id: 'files', label: 'Files', group: 'Tools', route: '/files' },
      { id: 'learning', label: 'Learning', group: 'Phase 2', route: '/learning' },
      { id: 'career', label: 'Career', group: 'Phase 2', route: '/career' },
      { id: 'finance', label: 'Finance', group: 'Phase 2', route: '/finance' },
      { id: 'analytics', label: 'Analytics', group: 'Phase 2', route: '/analytics' },
      { id: 'timeline', label: 'Timeline', group: 'Phase 2', route: '/timeline' },
      { id: 'reports', label: 'Reports', group: 'Phase 2', route: '/reports' },
      { id: 'memory', label: 'AI Memory', group: 'Phase 3', route: '/memory' },
      { id: 'coaches', label: 'AI Coaches', group: 'Phase 3', route: '/coaches' },
      { id: 'ocr', label: 'OCR', group: 'Phase 3', route: '/ocr' },
      { id: 'voice', label: 'Voice', group: 'Phase 3', route: '/voice' },
      { id: 'integrations', label: 'Integrations', group: 'Phase 3', route: '/integrations' },
      { id: 'automations', label: 'Automations', group: 'Phase 3', route: '/automations' },
      { id: 'predictions', label: 'Predictions', group: 'Phase 3', route: '/predictions' },
      { id: 'life-timeline', label: 'Life Timeline', group: 'Phase 3', route: '/life-timeline' },
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
