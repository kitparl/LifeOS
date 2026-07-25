import { Component, Input } from '@angular/core';
import { ChartPoint } from './chart-types';

@Component({
  selector: 'app-sparkline',
  standalone: true,
  template: `
    <svg [attr.viewBox]="'0 0 ' + width + ' ' + height" class="inline-block align-middle" [style.width.px]="width" [style.height.px]="height" role="img" [attr.aria-label]="title">
      <polyline
        fill="none"
        stroke="var(--primary)"
        stroke-width="1.5"
        [attr.points]="polyline"
      />
    </svg>
  `,
})
export class SparklineComponent {
  @Input() points: ChartPoint[] = [];
  @Input() title = 'Sparkline';
  @Input() width = 80;
  @Input() height = 24;

  get polyline(): string {
    if (!this.points.length) return '';
    const max = Math.max(...this.points.map((p) => p.value), 1);
    const n = this.points.length;
    return this.points
      .map((p, i) => {
        const x = (i / Math.max(n - 1, 1)) * this.width;
        const y = this.height - (p.value / max) * (this.height - 2) - 1;
        return `${x},${y}`;
      })
      .join(' ');
  }
}
