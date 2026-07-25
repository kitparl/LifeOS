import { Component, Input } from '@angular/core';
import { ChartPoint } from './chart-types';
import { ChartEmptyComponent } from './chart-empty.component';

@Component({
  selector: 'app-bar-chart',
  standalone: true,
  imports: [ChartEmptyComponent],
  template: `
    @if (!points.length) {
      <app-chart-empty />
    } @else {
      <svg [attr.viewBox]="'0 0 ' + width + ' ' + height" class="w-full h-auto" role="img" [attr.aria-label]="title">
        @for (b of bars; track b.i) {
          <rect
            [attr.x]="b.x"
            [attr.y]="b.y"
            [attr.width]="b.w"
            [attr.height]="b.h"
            fill="var(--primary)"
            rx="2"
          />
        }
      </svg>
      <div class="mt-1 flex justify-between gap-1 text-[10px] text-[var(--text-muted)] overflow-hidden">
        @for (p of points; track p.label) {
          <span class="truncate max-w-[4rem]" [title]="p.label">{{ p.label }}</span>
        }
      </div>
    }
  `,
})
export class BarChartComponent {
  @Input() points: ChartPoint[] = [];
  @Input() title = 'Bar chart';
  @Input() width = 320;
  @Input() height = 140;

  get bars(): { i: number; x: number; y: number; w: number; h: number }[] {
    if (!this.points.length) return [];
    const pad = 8;
    const max = Math.max(...this.points.map((p) => p.value), 1);
    const gap = 4;
    const n = this.points.length;
    const barW = Math.max((this.width - pad * 2 - gap * (n - 1)) / n, 2);
    return this.points.map((p, i) => {
      const h = (p.value / max) * (this.height - pad * 2);
      return {
        i,
        x: pad + i * (barW + gap),
        y: this.height - pad - h,
        w: barW,
        h,
      };
    });
  }
}
