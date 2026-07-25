import { Component, Input } from '@angular/core';
import { ChartPoint } from './chart-types';
import { ChartEmptyComponent } from './chart-empty.component';

@Component({
  selector: 'app-burndown-chart',
  standalone: true,
  imports: [ChartEmptyComponent],
  template: `
    @if (!points.length) {
      <app-chart-empty message="No burndown data" />
    } @else {
      <svg [attr.viewBox]="'0 0 ' + width + ' ' + height" class="w-full h-auto" role="img" [attr.aria-label]="title">
        <line
          [attr.x1]="pad"
          [attr.y1]="pad"
          [attr.x2]="width - pad"
          [attr.y2]="height - pad"
          stroke="var(--text-faint)"
          stroke-dasharray="4 3"
          stroke-width="1"
        />
        <polyline
          fill="none"
          stroke="var(--danger)"
          stroke-width="2"
          [attr.points]="polyline"
        />
      </svg>
    }
  `,
})
export class BurndownChartComponent {
  @Input() points: ChartPoint[] = [];
  @Input() title = 'Burndown';
  @Input() width = 320;
  @Input() height = 140;
  readonly pad = 12;

  get polyline(): string {
    if (!this.points.length) return '';
    const max = Math.max(...this.points.map((p) => p.value), 100);
    const n = this.points.length;
    return this.points
      .map((p, i) => {
        const x = this.pad + (i / Math.max(n - 1, 1)) * (this.width - this.pad * 2);
        const y = this.pad + (1 - p.value / max) * (this.height - this.pad * 2);
        return `${x},${y}`;
      })
      .join(' ');
  }
}
