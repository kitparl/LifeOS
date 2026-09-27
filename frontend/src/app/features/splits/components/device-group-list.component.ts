import { Component, input, output, signal } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { RouterLink } from '@angular/router';
import { DeviceSplitGroup } from '../models/split.models';
import { SplitPersonComponent } from './person.component';
import { SplitShareActionsComponent } from './share-actions.component';

/** "On this device": every group this browser created or joined, each removable from this device. */
@Component({
  selector: 'app-split-device-group-list',
  standalone: true,
  imports: [LucideDynamicIcon, RouterLink, SplitPersonComponent, SplitShareActionsComponent],
  template: `
    <div class="panel !p-0 overflow-hidden" data-testid="split-device-list">
      @if (groups().length) {
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (group of groups(); track group.code) {
            <li class="space-y-3 px-3 py-3" data-testid="split-device-row">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0 space-y-1">
                  <p class="truncate text-base font-semibold">{{ group.name }}</p>
                  <p class="flex items-center gap-1 text-xs" style="color: var(--text-muted)">
                    {{ group.role === 'creator' ? 'Created by' : 'Joined as' }}
                    <app-split-person [name]="group.displayName" [you]="true" />
                  </p>
                </div>
                <div class="flex shrink-0 items-center gap-2">
                  <a class="btn-primary text-sm" data-testid="split-device-open" [routerLink]="['/s', group.code]">Open</a>
                  <button
                    type="button"
                    class="btn-ghost inline-flex items-center gap-1 text-sm"
                    data-testid="split-device-remove"
                    [attr.aria-label]="'Remove ' + group.name + ' from this device'"
                    (click)="confirming.set(group.code)"
                  >
                    <svg class="h-4 w-4" lucideIcon="trash-2" aria-hidden="true"></svg>
                    Remove
                  </button>
                </div>
              </div>

              @if (confirming() === group.code) {
                <div class="space-y-2 rounded border border-[var(--xp-border)] p-2 text-xs" data-testid="split-device-remove-prompt">
                  <p>
                    Remove "{{ group.name }}" from this device? The group and its bills stay for everyone else. You
                    can still open the link, but you'd need to join again to add bills here.
                  </p>
                  <div class="flex gap-2">
                    <button
                      type="button"
                      class="btn-danger text-xs"
                      data-testid="split-device-remove-confirm"
                      (click)="confirming.set(null); remove.emit(group.code)"
                    >Remove</button>
                    <button type="button" class="btn-ghost text-xs" (click)="confirming.set(null)">Cancel</button>
                  </div>
                </div>
              }

              <app-split-share-actions [groupName]="group.name" [urlPath]="'/s/' + group.code" qrMode="toggle" />
            </li>
          }
        </ul>
      } @else {
        <p class="p-3 text-sm" style="color: var(--text-muted)">
          Groups you create or join on this phone stay listed here.
        </p>
      }
    </div>
  `,
})
export class SplitDeviceGroupListComponent {
  readonly groups = input.required<DeviceSplitGroup[]>();
  /** Emits the code of a group to forget on this device. */
  readonly remove = output<string>();

  /** The row whose "remove from this device" prompt is open. */
  readonly confirming = signal<string | null>(null);
}
