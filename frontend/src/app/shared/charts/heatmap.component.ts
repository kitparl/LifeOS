import { Component, Input } from '@angular/core';
import { HeatmapCell } from './chart-types';
import { ChartEmptyComponent } from './chart-empty.component';

@Component({
  selector: 'app-heatmap',
  standalone: true,
  imports: [ChartEmptyComponent],
  template: `
    @if (!cells.length) {
      <app-chart-empty />
    } @else {
      <div class="flex flex-wrap gap-1" role="img" [attr.aria-label]="title">
        @for (c of cells; track c.date) {
          <span
            class="h-3 w-3 border border-[var(--xp-border)]"
            [style.background]="cellColor(c)"
            [title]="c.date + ': ' + c.value"
          ></span>
        }
      </div>
    }
  `,
})
export class HeatmapComponent {
  @Input() cells: HeatmapCell[] = [];
  @Input() title = 'Heatmap';

  cellColor(c: HeatmapCell): string {
    if (c.completed || c.value > 0) {
      if (c.value >= 3) return 'var(--success)';
      if (c.value >= 1) return 'color-mix(in srgb, var(--success) 60%, var(--surface-2))';
      return 'var(--success)';
    }
    return 'var(--surface-3)';
  }
}
