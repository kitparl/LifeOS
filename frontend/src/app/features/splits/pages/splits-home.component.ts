import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { apiErrorMessage } from '../../../core/utils/http';
import { SplitCreateComponent } from '../components/split-create.component';
import { SplitDeviceGroupListComponent } from '../components/device-group-list.component';
import { SplitShareActionsComponent } from '../components/share-actions.component';
import { SplitGroupCreatePayload, SplitSeatIssued } from '../models/split.models';
import { SplitDeviceStoreService } from '../services/split-device-store.service';
import { SplitsApiService } from '../services/splits-api.service';

interface CreatedGroup {
  name: string;
  seat: SplitSeatIssued;
}

/**
 * Split bills home: create a group and see every group on this device. Same screen for
 * guests (`/explore/splits`) and signed-in users (`/splits`).
 */
@Component({
  selector: 'app-splits-home',
  standalone: true,
  imports: [RouterLink, SplitCreateComponent, SplitDeviceGroupListComponent, SplitShareActionsComponent],
  template: `
    <div class="mx-auto max-w-3xl space-y-4">
      <section class="panel space-y-3">
        <h2 class="text-sm font-semibold">New group</h2>
        @if (created(); as done) {
          <div class="space-y-3" data-testid="split-create-result">
            <p class="text-sm">
              <span class="font-medium">{{ done.name }}</span> is ready. Share the link — people join only if they want to.
            </p>
            <app-split-share-actions [groupName]="done.name" [urlPath]="done.seat.url_path" />
            <div class="flex flex-wrap gap-2">
              <a class="btn-primary text-xs" data-testid="split-open-created" [routerLink]="['/s', done.seat.code]">
                Open group
              </a>
              <button type="button" class="btn-ghost text-xs" (click)="created.set(null)">Create another</button>
            </div>
          </div>
        } @else {
          <app-split-create [busy]="busy()" (create)="create($event)" />
        }
        @if (error()) {
          <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
        }
      </section>

      <section class="space-y-2">
        <h2 class="text-sm font-semibold">On this device</h2>
        <app-split-device-group-list [groups]="store.groups()" />
      </section>
    </div>
  `,
})
export class SplitsHomeComponent {
  private readonly api = inject(SplitsApiService);
  protected readonly store = inject(SplitDeviceStoreService);

  readonly created = signal<CreatedGroup | null>(null);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);

  create(payload: SplitGroupCreatePayload): void {
    this.busy.set(true);
    this.error.set(null);
    this.api.createGroup(payload).subscribe({
      next: (seat) => {
        // Saved before any navigation so leaving the page never loses the link.
        this.store.save({
          code: seat.code,
          name: payload.name,
          seatSecret: seat.seat_secret,
          displayName: payload.creator_name,
          role: 'creator',
        });
        this.created.set({ name: payload.name, seat });
        this.busy.set(false);
      },
      error: (err: unknown) => {
        this.error.set(apiErrorMessage(err, 'Could not create the group.'));
        this.busy.set(false);
      },
    });
  }
}
