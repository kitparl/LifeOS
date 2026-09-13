import { DatePipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { RunningStats, formatDuration, formatPace } from '../models/running.models';

@Component({
  selector: 'app-running-bests-tab',
  standalone: true,
  imports: [RouterLink, DatePipe],
  host: { class: 'contents' },
  template: `
    <div class="panel !p-0 overflow-hidden">
      @if (stats) {
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr>
                <th class="px-3 py-2 text-left">Distance</th>
                <th class="px-3 py-2 text-left">Pace</th>
                <th class="px-3 py-2 text-left">Time</th>
                <th class="px-3 py-2 text-left">Date</th>
                <th class="px-3 py-2 text-left">Source</th>
              </tr>
            </thead>
            <tbody>
              @for (pb of stats.personal_bests; track pb.distance_type) {
                <tr style="border-bottom: 1px solid var(--border)">
                  <td class="px-3 py-2 font-medium">{{ pb.label }}</td>
                  <td class="px-3 py-2">{{ pb.pace_min_per_km ? formatPace(pb.pace_min_per_km) : '—' }}</td>
                  <td class="px-3 py-2">{{ pb.duration_seconds ? formatDuration(pb.duration_seconds) : '—' }}</td>
                  <td class="px-3 py-2" style="color: var(--text-muted)">
                    {{ pb.run_date ? (pb.run_date | date: 'mediumDate') : '—' }}
                  </td>
                  <td class="px-3 py-2">
                    @if (pb.source === 'race' && pb.source_id) {
                      <a [routerLink]="['/running/races', pb.source_id]" class="link text-sm">{{ pb.source_name || 'Event' }}</a>
                    } @else if (pb.source === 'run' && pb.source_id) {
                      <a [routerLink]="['/running', pb.source_id]" class="link text-sm">{{ pb.source_name || 'Log run' }}</a>
                    } @else {
                      —
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
})
export class RunningBestsTabComponent {
  @Input() stats: RunningStats | null = null;

  readonly formatDuration = formatDuration;
  readonly formatPace = formatPace;
}
