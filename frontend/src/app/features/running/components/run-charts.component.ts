import { Component, Input, OnChanges } from '@angular/core';
import { LineChartComponent } from '../../../shared/charts/line-chart.component';
import { ChartPoint } from '../../../shared/charts/chart-types';
import { ChartChannel, chartPoints, paceLabel } from '../activity.utils';
import { ActivitySeries } from '../models/activity.models';

interface ChartSpec {
  id: ChartChannel;
  title: string;
  points: ChartPoint[];
  caption: string;
}

const CHARTS: { id: ChartChannel; title: string; unit: string }[] = [
  { id: 'pace', title: 'Pace', unit: '' },
  { id: 'heart_rate', title: 'Heart rate', unit: ' bpm' },
  { id: 'altitude_m', title: 'Elevation', unit: ' m' },
  { id: 'cadence', title: 'Cadence', unit: ' spm' },
];

@Component({
  selector: 'app-run-charts',
  standalone: true,
  imports: [LineChartComponent],
  host: { class: 'contents' },
  template: `
    @if (charts.length) {
      <div class="grid gap-3 md:grid-cols-2" data-testid="run-charts">
        @for (c of charts; track c.id) {
          <div class="panel">
            <p class="text-xs" style="color: var(--text-muted)">{{ c.title }} over distance</p>
            <p class="text-xs mb-1" style="color: var(--text-muted)">{{ c.caption }}</p>
            <app-line-chart
              [points]="c.points"
              [title]="c.title + ' chart'"
              [width]="480"
              [height]="140"
              [fitRange]="true"
              [showPoints]="false"
            />
          </div>
        }
      </div>
    }
  `,
})
export class RunChartsComponent implements OnChanges {
  @Input({ required: true }) series!: ActivitySeries;

  charts: ChartSpec[] = [];

  ngOnChanges(): void {
    this.charts = CHARTS.flatMap((spec) => {
      const points = chartPoints(this.series, spec.id);
      if (points.length < 2) return [];
      const values = points.map((p) => p.value);
      const lo = Math.min(...values);
      const hi = Math.max(...values);
      const caption =
        spec.id === 'pace'
          ? `${paceLabel(lo * 60)} to ${paceLabel(hi * 60)}`
          : `${Math.round(lo)} to ${Math.round(hi)}${spec.unit}`;
      return [{ id: spec.id, title: spec.title, points, caption }];
    });
  }
}
