import { Component, HostListener, computed, inject, signal } from '@angular/core';
import { HomePreferencesService } from '../../core/services/home-preferences.service';
import { getDestinationById } from '../../shared/layout/nav-registry';

@Component({
  selector: 'app-settings-home-section',
  standalone: true,
  template: `
    <div class="space-y-3">
      <p class="text-sm text-[var(--text-muted)]">
        Choose which module opens when you visit the home URL.
      </p>

      <div class="panel !p-0">
        <div class="title-bar">Default home</div>
        <div class="p-3">
          <label class="mb-1 block text-sm" for="default-home-module">Module</label>
          <div class="home-module-select type-select">
            <button
              id="default-home-module"
              type="button"
              class="type-select__control w-full"
              [class.type-select__control--open]="open()"
              [attr.aria-expanded]="open()"
              aria-haspopup="listbox"
              (click)="toggle()"
            >
              <span class="type-select__input">{{ selectedLabel() }}</span>
              <span class="type-select__caret" aria-hidden="true">▾</span>
            </button>

            @if (open()) {
              <div class="type-select__menu home-module-select__menu">
                <input
                  class="input-field home-module-select__search"
                  type="search"
                  placeholder="Search modules"
                  autofocus
                  [value]="query()"
                  (input)="query.set($any($event.target).value)"
                  (keydown)="onSearchKeydown($event)"
                />
                <div class="home-module-select__options" role="listbox">
                  @for (group of filteredGroups(); track group.category) {
                    <p
                      class="px-2 py-1 text-xs font-semibold uppercase tracking-wide"
                      style="color: var(--text-muted)"
                    >
                      {{ group.category }}
                    </p>
                    @for (item of group.items; track item.id) {
                      <button
                        type="button"
                        class="type-select__option"
                        role="option"
                        [class.active]="homePrefs.moduleId() === item.id"
                        [attr.aria-selected]="homePrefs.moduleId() === item.id"
                        (click)="choose(item.id)"
                      >
                        {{ item.label }}
                      </button>
                    }
                  } @empty {
                    <div class="type-select__empty">No matches</div>
                  }
                </div>
              </div>
            }
          </div>
        </div>
      </div>
    </div>

    <style>
      .home-module-select .type-select__control {
        font: inherit;
        color: inherit;
        cursor: pointer;
      }
      .home-module-select__menu {
        display: flex;
        flex-direction: column;
        overflow: hidden;
        max-height: 280px;
      }
      .home-module-select__search {
        flex-shrink: 0;
        margin: 0.15rem 0.15rem 0.35rem;
      }
      .home-module-select__options {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
      }
    </style>
  `,
})
export class SettingsHomeSectionComponent {
  readonly homePrefs = inject(HomePreferencesService);
  readonly open = signal(false);
  readonly query = signal('');
  readonly selectedLabel = computed(
    () => getDestinationById(this.homePrefs.moduleId())?.label ?? this.homePrefs.moduleId(),
  );
  readonly filteredGroups = computed(() => {
    const q = this.query().trim().toLowerCase();
    return this.homePrefs.groupedOptions
      .map((group) => ({
        category: group.category,
        items: q
          ? group.items.filter((item) => this.matchesQuery(item.label, item.id, item.shortLabel, item.category, q))
          : group.items,
      }))
      .filter((group) => group.items.length > 0);
  });

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!(event.target as HTMLElement).closest('.home-module-select')) {
      this.closeMenu();
    }
  }

  toggle(): void {
    if (this.open()) {
      this.closeMenu();
      return;
    }
    this.query.set('');
    this.open.set(true);
  }

  choose(moduleId: string): void {
    this.homePrefs.setModuleId(moduleId);
    this.closeMenu();
  }

  onSearchKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault();
      this.closeMenu();
      return;
    }
    if (event.key === 'Enter') {
      event.preventDefault();
      const first = this.filteredGroups()[0]?.items[0];
      if (first) this.choose(first.id);
    }
  }

  private closeMenu(): void {
    this.open.set(false);
    this.query.set('');
  }

  private matchesQuery(
    label: string,
    id: string,
    shortLabel: string | undefined,
    category: string | undefined,
    query: string,
  ): boolean {
    return [label, id, shortLabel, category].some((value) => value?.toLowerCase().includes(query));
  }
}
