import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
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
              (ngModelChange)="palette.setQuery($event)"
              (keydown)="onInputKeydown($event)"
            />
          </div>
          <ul class="max-h-72 overflow-y-auto text-sm">
            @for (item of filtered; track item.id; let i = $index) {
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
export class CommandPaletteComponent implements OnInit {
  readonly palette = inject(CommandPaletteService);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);

  get filtered(): CommandPaletteItem[] {
    return this.palette.filteredItems();
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
    ]);
  }

  onInputKeydown(event: KeyboardEvent): void {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.palette.moveActive(1);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.palette.moveActive(-1);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const item = this.palette.selectActive();
      if (item) {
        this.run(item);
      }
    }
  }

  run(item: CommandPaletteItem): void {
    if (item.disabled) {
      return;
    }
    this.palette.close();
    if (item.action) {
      item.action();
    } else if (item.route) {
      this.router.navigateByUrl(item.route);
    }
  }
}
