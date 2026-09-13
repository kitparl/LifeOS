import { Component, Input } from '@angular/core';
import { BarChartComponent } from '../../../shared/charts/bar-chart.component';
import { LineChartComponent } from '../../../shared/charts/line-chart.component';
import { RunningStats } from '../models/running.models';

@Component({
  selector: 'app-running-stats-tab',
  standalone: true,
  imports: [LineChartComponent, BarChartComponent],
  host: { class: 'contents' },
  template: `
    <div class="grid gap-3 lg:grid-cols-2">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Distance over time</div>
        <div class="p-3">
          <app-line-chart [points]="stats?.distance_over_time || []" title="Distance over time" />
        </div>
      </div>
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Weekly totals</div>
        <div class="p-3">
          <app-bar-chart [points]="stats?.weekly_totals || []" title="Weekly totals" />
        </div>
      </div>
    </div>
  `,
})
export class RunningStatsTabComponent {
  @Input() stats: RunningStats | null = null;
}
