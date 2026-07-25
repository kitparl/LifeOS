import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-widget-frame',
  standalone: true,
  template: `
    <div class="panel !p-0 overflow-hidden">
      <div class="title-bar flex items-center justify-between gap-2 px-3 py-2 text-sm font-medium">
        <span>{{ title }}</span>
        @if (hint) {
          <span class="text-xs font-normal text-[var(--text-muted)]">{{ hint }}</span>
        }
      </div>
      <div class="p-3">
        <ng-content />
      </div>
    </div>
  `,
})
export class WidgetFrameComponent {
  @Input({ required: true }) title!: string;
  @Input() hint: string | null = null;
}
