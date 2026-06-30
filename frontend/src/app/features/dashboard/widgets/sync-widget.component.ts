import { Component, Input } from '@angular/core';
import { SyncStatus } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-sync-widget',
  standalone: true,
  imports: [WidgetSkeletonComponent],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0">Sync Status</div>
      @if (loading) {
        <app-widget-skeleton />
      } @else {
        <div class="p-3 text-sm space-y-1">
          <p class="flex items-center gap-2">
            <span class="inline-block h-2 w-2 rounded-full" [class]="statusClass"></span>
            <span class="font-medium capitalize">{{ syncStatus }}</span>
          </p>
          @if (pendingCount > 0) {
            <p class="text-xs text-orange-700">{{ pendingCount }} pending change(s)</p>
          } @else {
            <p class="text-xs text-gray-600">Everything is up to date</p>
          }
        </div>
      }
    </div>
  `,
})
export class SyncWidgetComponent {
  @Input() loading = false;
  @Input() syncStatus: SyncStatus = 'synced';
  @Input() pendingCount = 0;

  get statusClass(): string {
    switch (this.syncStatus) {
      case 'syncing':
        return 'bg-orange-500';
      case 'offline':
        return 'bg-gray-500';
      default:
        return 'bg-green-600';
    }
  }
}
