import { Component, computed, inject } from '@angular/core';
import { CdkDragDrop, CdkDropList, CdkDrag, CdkDragHandle, CdkDragPlaceholder } from '@angular/cdk/drag-drop';
import { LucideDynamicIcon } from '@lucide/angular';
import { NavPreferencesService } from '../../core/services/nav-preferences.service';
import { NAV_CATEGORIES_ENABLED, NavDestination } from '../../shared/layout/nav-registry';

@Component({
  selector: 'app-settings-sidebar-section',
  standalone: true,
  imports: [CdkDropList, CdkDrag, CdkDragHandle, CdkDragPlaceholder, LucideDynamicIcon],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-start justify-between gap-2">
        <details class="sidebar-help text-sm">
          <summary class="link cursor-pointer select-none">How this works</summary>
          <ul class="mt-2 list-disc space-y-1 pl-5" style="color: var(--text-muted)">
            <li><strong>Show</strong> adds or removes a module from the sidebar. Hidden modules stay reachable via Search (⌘K).</li>
            <li><strong>Pin</strong> keeps a module at the top of the sidebar.</li>
            <li>Drag the <span aria-hidden="true">⋮⋮</span> handle to reorder modules within their section.</li>
          </ul>
        </details>
        <button type="button" class="btn-secondary text-xs" (click)="navPrefs.resetToDefault()">Reset to defaults</button>
      </div>

      <div class="panel !p-0 overflow-hidden">
        <div class="sidebar-settings-row sidebar-settings-head" aria-hidden="true">
          <span class="sidebar-settings-drag sidebar-settings-drag--disabled"></span>
          <span class="flex-1">Module</span>
          <span class="sidebar-settings-col">Pin</span>
          <span class="sidebar-settings-col">Show</span>
        </div>

        @for (group of settingsGroups(); track group.category) {
          <div class="border-b border-[var(--border)]">
            @if (navCategoriesEnabled) {
              <p class="sidebar-settings-group">{{ group.category }}</p>
            }
            <ul
              class="divide-y divide-[var(--border)] text-sm"
              cdkDropList
              [id]="'nav-cat-' + group.category"
              (cdkDropListDropped)="onDrop(group.category, $event)"
            >
              @for (item of group.items; track item.id) {
                <li class="sidebar-settings-row" cdkDrag>
                  <span class="sidebar-settings-drag" title="Drag to reorder" aria-hidden="true" cdkDragHandle>⋮⋮</span>

                  <div class="min-w-0 flex-1 flex items-center gap-2">
                    @if (item.icon) {
                      <svg class="settings-nav-icon" [lucideIcon]="item.icon" aria-hidden="true"></svg>
                    }
                    <span class="truncate">{{ item.label }}</span>
                  </div>

                  <span class="sidebar-settings-col">
                    <button
                      type="button"
                      class="btn-ghost sidebar-settings-pin"
                      [class.sidebar-settings-pin--on]="navPrefs.isPinnedTop(item.id)"
                      [title]="navPrefs.isPinnedTop(item.id) ? 'Unpin from top' : 'Pin to top'"
                      [attr.aria-label]="(navPrefs.isPinnedTop(item.id) ? 'Unpin ' : 'Pin ') + item.label"
                      [attr.aria-pressed]="navPrefs.isPinnedTop(item.id)"
                      (click)="navPrefs.togglePinTop(item.id)"
                    >
                      <svg
                        class="settings-nav-icon"
                        [lucideIcon]="navPrefs.isPinnedTop(item.id) ? 'pin' : 'pin-off'"
                        aria-hidden="true"
                      ></svg>
                    </button>
                  </span>

                  <span class="sidebar-settings-col">
                    <label class="toggle-switch sidebar-settings-toggle" title="Hide from sidebar">
                      <input
                        type="checkbox"
                        [checked]="true"
                        [attr.aria-label]="'Show ' + item.label + ' in sidebar'"
                        (change)="navPrefs.togglePin(item.id)"
                      />
                      <span class="toggle-switch__track" aria-hidden="true"></span>
                    </label>
                  </span>

                  <div *cdkDragPlaceholder class="sidebar-settings-placeholder"></div>
                </li>
              }
            </ul>
          </div>
        }

        @if (navPrefs.unpinnedDestinations().length > 0) {
          <p class="sidebar-settings-group">Hidden</p>
          <ul class="divide-y divide-[var(--border)] text-sm">
            @for (item of navPrefs.unpinnedDestinations(); track item.id) {
              <li class="sidebar-settings-row">
                <span class="sidebar-settings-drag sidebar-settings-drag--disabled" aria-hidden="true"></span>

                <div class="min-w-0 flex-1 flex items-center gap-2">
                  @if (item.icon) {
                    <svg class="settings-nav-icon" [lucideIcon]="item.icon" aria-hidden="true"></svg>
                  }
                  <span class="truncate">{{ item.label }}</span>
                  @if (navCategoriesEnabled && item.category) {
                    <span class="hidden text-xs text-[var(--text-muted)] sm:inline">{{ item.category }}</span>
                  }
                </div>

                <span class="sidebar-settings-col"></span>

                <span class="sidebar-settings-col">
                  <label class="toggle-switch sidebar-settings-toggle" title="Show in sidebar">
                    <input
                      type="checkbox"
                      [checked]="false"
                      [attr.aria-label]="'Show ' + item.label + ' in sidebar'"
                      (change)="navPrefs.togglePin(item.id)"
                    />
                    <span class="toggle-switch__track" aria-hidden="true"></span>
                  </label>
                </span>
              </li>
            }
          </ul>
        }
      </div>
    </div>

    <style>
      .settings-nav-icon {
        width: 1rem;
        height: 1rem;
        flex-shrink: 0;
        color: var(--text-muted);
        stroke: currentColor;
      }
      .sidebar-settings-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        min-height: 44px;
        padding: 0.25rem 0.75rem 0.25rem 0.25rem;
        background: var(--surface);
      }
      .sidebar-settings-head {
        min-height: 0;
        padding-block: 0.4rem;
        font-size: 0.6875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        background: var(--surface-2);
        border-bottom: 1px solid var(--border);
      }
      .sidebar-settings-group {
        padding: 0.375rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text);
        background: var(--surface-2);
      }
      .sidebar-settings-col {
        display: inline-flex;
        justify-content: center;
        flex-shrink: 0;
        width: 2.75rem;
        text-align: center;
      }
      .sidebar-settings-pin {
        width: 2.25rem;
        min-height: 2.25rem;
        padding: 0 !important;
      }
      .sidebar-settings-pin--on .settings-nav-icon {
        color: var(--primary);
      }
      .sidebar-settings-toggle {
        min-height: 2.25rem;
      }
      .sidebar-settings-drag {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        width: 2rem;
        min-height: 2.5rem;
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
        min-height: 0;
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
  readonly navCategoriesEnabled = NAV_CATEGORIES_ENABLED;

  readonly settingsGroups = computed(() => this.navPrefs.navGroups());

  onDrop(category: string, event: CdkDragDrop<NavDestination[]>): void {
    if (event.previousIndex === event.currentIndex) return;
    this.navPrefs.reorderWithinCategory(category, event.previousIndex, event.currentIndex);
  }
}
