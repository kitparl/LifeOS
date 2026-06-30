import { Component, Input, inject } from '@angular/core';
import { Router } from '@angular/router';
import { QuickActionItem } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-quick-actions-widget',
  standalone: true,
  imports: [WidgetSkeletonComponent],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0">Quick Actions</div>
      @if (loading) {
        <app-widget-skeleton />
      } @else {
        <div class="flex flex-wrap gap-2 p-3">
          @for (action of actions; track action.id) {
            <button
              type="button"
              class="btn-primary text-xs"
              [disabled]="!action.enabled"
              [class.opacity-50]="!action.enabled"
              (click)="run(action)"
            >
              {{ action.label }}
            </button>
          }
        </div>
      }
    </div>
  `,
})
export class QuickActionsWidgetComponent {
  private readonly router = inject(Router);

  @Input() loading = false;
  @Input() actions: QuickActionItem[] = [];

  run(action: QuickActionItem): void {
    if (!action.enabled || !action.route) return;
    this.router.navigateByUrl(action.route);
  }
}
