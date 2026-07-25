import { Component, Input } from '@angular/core';
import { ChartPoint } from './chart-types';
import { ChartEmptyComponent } from './chart-empty.component';

@Component({
  selector: 'app-donut-chart',
  standalone: true,
  imports: [ChartEmptyComponent],
  template: `
    @if (!points.length) {
      <app-chart-empty />
    } @else {
      <div class="flex items-center gap-4">
        <svg viewBox="0 0 42 42" class="h-28 w-28 shrink-0" role="img" [attr.aria-label]="title">
          @for (s of slices; track s.i) {
            <circle
              cx="21"
              cy="21"
              r="15.915"
              fill="transparent"
              [attr.stroke]="s.color"
              stroke-width="6"
              [attr.stroke-dasharray]="s.dash"
              [attr.stroke-dashoffset]="s.offset"
            />
          }
        </svg>
        <ul class="space-y-1 text-xs">
          @for (p of points; track p.label; let i = $index) {
            <li class="flex items-center gap-2">
              <span class="inline-block h-2 w-2 rounded-full" [style.background]="colors[i % colors.length]"></span>
              <span class="text-[var(--text-muted)]">{{ p.label }}</span>
              <span class="font-medium">{{ p.value }}</span>
            </li>
          }
        </ul>
      </div>
    }
  `,
})
export class DonutChartComponent {
  @Input() points: ChartPoint[] = [];
  @Input() title = 'Donut chart';

  readonly colors = [
    'var(--primary)',
    'var(--success)',
    'var(--warning)',
    'var(--danger)',
    'var(--info)',
    'var(--text-muted)',
  ];

  get slices(): { i: number; color: string; dash: string; offset: number }[] {
    const total = this.points.reduce((s, p) => s + p.value, 0) || 1;
    let cumulative = 0;
    return this.points.map((p, i) => {
      const pct = (p.value / total) * 100;
      const offset = 25 - cumulative;
      cumulative += pct;
      return {
        i,
        color: this.colors[i % this.colors.length],
        dash: `${pct} ${100 - pct}`,
        offset,
      };
    });
  }
}
