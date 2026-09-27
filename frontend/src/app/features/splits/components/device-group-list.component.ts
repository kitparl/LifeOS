import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DeviceSplitGroup } from '../models/split.models';
import { SplitShareActionsComponent } from './share-actions.component';

/** "On this device": every group this browser created or joined. */
@Component({
  selector: 'app-split-device-group-list',
  standalone: true,
  imports: [RouterLink, SplitShareActionsComponent],
  template: `
    <div class="panel !p-0 overflow-hidden" data-testid="split-device-list">
      @if (groups().length) {
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (group of groups(); track group.code) {
            <li class="space-y-2 px-3 py-3" data-testid="split-device-row">
              <div class="flex items-center justify-between gap-2">
                <p class="min-w-0 truncate font-medium">
                  {{ group.name }}
                  <span class="text-xs font-normal" style="color: var(--text-muted)">
                    · {{ group.displayName }}{{ group.role === 'creator' ? ' (creator)' : '' }}
                  </span>
                </p>
                <a class="btn-primary shrink-0 text-xs" data-testid="split-device-open" [routerLink]="['/s', group.code]">
                  Open
                </a>
              </div>
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
}
