import { Component, Input } from '@angular/core';
import { ChartPoint } from './chart-types';
import { ChartEmptyComponent } from './chart-empty.component';

@Component({
  selector: 'app-line-chart',
  standalone: true,
  imports: [ChartEmptyComponent],
  template: `
    @if (!points.length) {
      <app-chart-empty />
    } @else {
      <svg [attr.viewBox]="'0 0 ' + width + ' ' + height" class="w-full h-auto" role="img" [attr.aria-label]="title">
        <polyline
          fill="none"
          stroke="var(--primary)"
          stroke-width="2"
          [attr.points]="polyline"
        />
        @if (showPoints) {
          @for (p of mapped; track p.i) {
            <circle [attr.cx]="p.x" [attr.cy]="p.y" r="3" fill="var(--primary)" />
          }
        }
      </svg>
    }
  `,
})
export class LineChartComponent {
  @Input() points: ChartPoint[] = [];
  @Input() title = 'Line chart';
  @Input() width = 320;
  @Input() height = 140;
  /** Scale between the lowest and highest value instead of from zero (for pace, heart rate, elevation). */
  @Input() fitRange = false;
  /** Draw a dot at every point; turn off for long series. */
  @Input() showPoints = true;

  get mapped(): { i: number; x: number; y: number }[] {
    if (!this.points.length) return [];
    const pad = 12;
    const values = this.points.map((p) => p.value);
    const min = this.fitRange ? Math.min(...values) : 0;
    const max = this.fitRange ? Math.max(...values) : Math.max(...values, 1);
    const span = max - min || 1;
    const n = this.points.length;
    return this.points.map((p, i) => ({
      i,
      x: pad + (i / Math.max(n - 1, 1)) * (this.width - pad * 2),
      y: this.height - pad - ((p.value - min) / span) * (this.height - pad * 2),
    }));
  }

  get polyline(): string {
    return this.mapped.map((p) => `${p.x},${p.y}`).join(' ');
  }
}
