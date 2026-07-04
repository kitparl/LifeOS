import { Component, inject } from '@angular/core';
import { NavPreferencesService } from '../../core/services/nav-preferences.service';

@Component({
  selector: 'app-settings-sidebar-section',
  standalone: true,
  template: `
    <div class="space-y-3">
      <p class="text-sm text-[var(--text-muted)]">
        Choose which destinations appear in your sidebar. Unpinned items remain available via Search and the command palette.
      </p>
      <button type="button" class="btn-primary text-xs" (click)="navPrefs.resetToDefault()">Reset to defaults</button>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Pinned in sidebar</div>
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (item of navPrefs.pinnedDestinations(); track item.id; let i = $index) {
            <li class="flex items-center justify-between gap-2 px-3 py-2">
              <span>{{ item.label }}</span>
              <div class="flex shrink-0 items-center gap-1">
                <button type="button" class="input-field !min-h-8 !w-auto px-2 text-xs" [disabled]="i === 0" (click)="navPrefs.moveUp(item.id)">Up</button>
                <button
                  type="button"
                  class="input-field !min-h-8 !w-auto px-2 text-xs"
                  [disabled]="i === navPrefs.pinnedDestinations().length - 1"
                  (click)="navPrefs.moveDown(item.id)"
                >
                  Down
                </button>
                <button type="button" class="text-xs text-red-700 underline" (click)="navPrefs.unpin(item.id)">Remove</button>
              </div>
            </li>
          } @empty {
            <li class="px-3 py-4 text-[var(--text-muted)]">No pinned destinations.</li>
          }
        </ul>
      </div>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Available to add</div>
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (item of navPrefs.unpinnedDestinations(); track item.id) {
            <li class="flex items-center justify-between gap-2 px-3 py-2">
              <div>
                <span>{{ item.label }}</span>
                @if (item.category) {
                  <span class="ml-2 text-xs text-[var(--text-muted)]">{{ item.category }}</span>
                }
              </div>
              <button type="button" class="btn-primary text-xs" (click)="navPrefs.pin(item.id)">Add to sidebar</button>
            </li>
          } @empty {
            <li class="px-3 py-4 text-[var(--text-muted)]">All destinations are pinned.</li>
          }
        </ul>
      </div>
    </div>
  `,
})
export class SettingsSidebarSectionComponent {
  readonly navPrefs = inject(NavPreferencesService);
}
