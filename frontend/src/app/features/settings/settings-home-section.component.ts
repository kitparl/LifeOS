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
              <div class="type-select__menu" role="listbox">
                @for (group of homePrefs.groupedOptions; track group.category) {
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
                }
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
    </style>
  `,
})
export class SettingsHomeSectionComponent {
  readonly homePrefs = inject(HomePreferencesService);
  readonly open = signal(false);
  readonly selectedLabel = computed(
    () => getDestinationById(this.homePrefs.moduleId())?.label ?? this.homePrefs.moduleId(),
  );

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!(event.target as HTMLElement).closest('.home-module-select')) {
      this.open.set(false);
    }
  }

  toggle(): void {
    this.open.set(!this.open());
  }

  choose(moduleId: string): void {
    this.homePrefs.setModuleId(moduleId);
    this.open.set(false);
  }
}
