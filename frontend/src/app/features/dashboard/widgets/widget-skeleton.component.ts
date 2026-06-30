import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-widget-skeleton',
  standalone: true,
  template: `
    <div class="animate-pulse space-y-2 p-3">
      <div class="h-3 w-2/3 rounded bg-gray-300"></div>
      <div class="h-3 w-full rounded bg-gray-200"></div>
      <div class="h-3 w-4/5 rounded bg-gray-200"></div>
    </div>
  `,
})
export class WidgetSkeletonComponent {
  @Input() lines = 3;
}
