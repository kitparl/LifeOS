import { Component, computed, inject } from '@angular/core';
import { CdkDragDrop, CdkDropList, CdkDrag, CdkDragHandle, CdkDragPlaceholder } from '@angular/cdk/drag-drop';
import { NavPreferencesService } from '../../core/services/nav-preferences.service';
import { NavDestination } from '../../shared/layout/nav-registry';

@Component({
  selector: 'app-settings-sidebar-section',
  standalone: true,
  imports: [CdkDropList, CdkDrag, CdkDragHandle, CdkDragPlaceholder],
  template: `
    <div class="space-y-3">
      <p class="text-sm text-[var(--text-muted)]">
        Toggle destinations on or off for your sidebar. Drag within a category (or Pin) to reorder.
        Pin-to-top moves a module into the Pin group at the top of the sidebar.
        Unpinned items remain available via Search and the command palette.
      </p>
      <button type="button" class="btn-primary text-xs" (click)="navPrefs.resetToDefault()">Reset to defaults</button>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar">Navigation</div>

        @for (group of settingsGroups(); track group.category) {
          <div class="border-b border-[var(--border)]">
            <p class="px-3 py-1.5 text-xs font-semibold uppercase tracking-wide" style="color: var(--text-muted); background: var(--surface-2)">
              {{ group.category }}
            </p>
            <ul
              class="divide-y divide-[var(--border)] text-sm"
              cdkDropList
              [id]="'nav-cat-' + group.category"
              (cdkDropListDropped)="onDrop(group.category, $event)"
            >
              @for (item of group.items; track item.id) {
                <li class="sidebar-settings-row sidebar-settings-row--pinned" cdkDrag>
                  <span class="sidebar-settings-drag" title="Drag to reorder" aria-hidden="true" cdkDragHandle>⋮⋮</span>

                  <div class="min-w-0 flex-1">
                    <span>{{ item.label }}</span>
                  </div>

                  <button
                    type="button"
                    class="btn-ghost !px-2 text-xs"
                    [title]="navPrefs.isPinnedTop(item.id) ? 'Unpin from top' : 'Pin to top'"
                    (click)="navPrefs.togglePinTop(item.id)"
                  >
                    {{ navPrefs.isPinnedTop(item.id) ? '📌' : '📍' }}
                  </button>

                  <label class="toggle-switch" title="Remove from sidebar">
                    <input type="checkbox" [checked]="true" (change)="navPrefs.togglePin(item.id)" />
                    <span class="toggle-switch__track" aria-hidden="true"></span>
                  </label>

                  <div *cdkDragPlaceholder class="sidebar-settings-placeholder"></div>
                </li>
              }
            </ul>
          </div>
        }

        @if (navPrefs.unpinnedDestinations().length > 0) {
          <p class="px-3 py-1.5 text-xs font-semibold uppercase tracking-wide" style="color: var(--text-muted); background: var(--surface-2)">
            Available
          </p>
          <ul class="divide-y divide-[var(--border)] text-sm">
            @for (item of navPrefs.unpinnedDestinations(); track item.id) {
              <li class="sidebar-settings-row">
                <span class="sidebar-settings-drag sidebar-settings-drag--disabled" aria-hidden="true"></span>

                <div class="min-w-0 flex-1">
                  <span>{{ item.label }}</span>
                  @if (item.category) {
                    <span class="ml-2 text-xs text-[var(--text-muted)]">{{ item.category }}</span>
                  }
                </div>

                <label class="toggle-switch" title="Add to sidebar">
                  <input type="checkbox" [checked]="false" (change)="navPrefs.togglePin(item.id)" />
                  <span class="toggle-switch__track" aria-hidden="true"></span>
                </label>
              </li>
            }
          </ul>
        }
      </div>
    </div>

    <style>
      .sidebar-settings-row {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        padding: 0.625rem 0.875rem;
        transition: background 120ms ease;
        background: var(--surface);
      }
      .sidebar-settings-row--pinned {
        cursor: default;
      }
      .sidebar-settings-drag {
        flex-shrink: 0;
        width: 1rem;
        font-size: 0.75rem;
        line-height: 1;
        color: var(--text-muted);
        letter-spacing: -2px;
        user-select: none;
        cursor: grab;
        touch-action: none;
      }
      .sidebar-settings-drag:active {
        cursor: grabbing;
      }
      .sidebar-settings-drag--disabled {
        visibility: hidden;
        cursor: default;
      }
      .sidebar-settings-placeholder {
        height: 44px;
        background: var(--primary-soft);
        border-radius: 4px;
        width: 100%;
      }
      .cdk-drag-preview {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        padding: 0.625rem 0.875rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 4px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        font-size: 0.875rem;
        color: var(--text);
        list-style: none;
      }
      .cdk-drag-animating {
        transition: transform 250ms cubic-bezier(0, 0, 0.2, 1);
      }
      .cdk-drop-list-dragging li:not(.cdk-drag-placeholder) {
        transition: transform 250ms cubic-bezier(0, 0, 0.2, 1);
      }
    </style>
  `,
})
export class SettingsSidebarSectionComponent {
  readonly navPrefs = inject(NavPreferencesService);

  readonly settingsGroups = computed(() => this.navPrefs.navGroups());

  onDrop(category: string, event: CdkDragDrop<NavDestination[]>): void {
    if (event.previousIndex === event.currentIndex) return;
    this.navPrefs.reorderWithinCategory(category, event.previousIndex, event.currentIndex);
  }
}
