import { DecimalPipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { clockLabel, paceLabel } from '../activity.utils';
import { ActivityLap, ActivitySplit } from '../models/activity.models';

@Component({
  selector: 'app-run-splits-table',
  standalone: true,
  host: { class: 'contents' },
  template: `
    @if (splits.length) {
      <div class="panel !p-0 overflow-hidden" data-testid="run-splits-table">
        <div class="title-bar">Splits</div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm" style="min-width: 420px">
            <thead>
              <tr>
                <th class="px-3 py-2 text-left">Km</th>
                <th class="px-3 py-2 text-left">Time</th>
                <th class="px-3 py-2 text-left">Pace</th>
                <th class="px-3 py-2 text-left">Heart rate</th>
                <th class="px-3 py-2 text-left">Elevation</th>
                <th class="px-3 py-2 text-left">Cadence</th>
              </tr>
            </thead>
            <tbody>
              @for (s of splits; track s.index) {
                <tr style="border-bottom: 1px solid var(--border)">
                  <td class="px-3 py-2">{{ splitLabel(s) }}</td>
                  <td class="px-3 py-2">{{ clock(s.duration_s) }}</td>
                  <td class="px-3 py-2">{{ pace(s.pace_s_per_km) }}</td>
                  <td class="px-3 py-2">{{ s.avg_hr !== null ? (s.avg_hr | number: '1.0-0') + ' bpm' : '—' }}</td>
                  <td class="px-3 py-2">{{ elevation(s.elevation_change_m) }}</td>
                  <td class="px-3 py-2">{{ s.avg_cadence !== null ? (s.avg_cadence | number: '1.0-0') + ' spm' : '—' }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    }

    @if (laps.length > 1) {
      <div class="panel !p-0 overflow-hidden" data-testid="run-laps-table">
        <div class="title-bar">Laps</div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm" style="min-width: 460px">
            <thead>
              <tr>
                <th class="px-3 py-2 text-left">Lap</th>
                <th class="px-3 py-2 text-left">Distance</th>
                <th class="px-3 py-2 text-left">Time</th>
                <th class="px-3 py-2 text-left">Pace</th>
                <th class="px-3 py-2 text-left">Heart rate</th>
                <th class="px-3 py-2 text-left">Ascent</th>
              </tr>
            </thead>
            <tbody>
              @for (l of laps; track l.index) {
                <tr style="border-bottom: 1px solid var(--border)">
                  <td class="px-3 py-2">{{ l.index }}</td>
                  <td class="px-3 py-2">{{ (l.distance_m / 1000) | number: '1.2-2' }} km</td>
                  <td class="px-3 py-2">{{ clock(l.duration_s) }}</td>
                  <td class="px-3 py-2">{{ pace(lapPace(l)) }}</td>
                  <td class="px-3 py-2">{{ l.avg_hr !== null ? l.avg_hr + ' bpm' : '—' }}</td>
                  <td class="px-3 py-2">{{ l.elevation_gain_m !== null ? '+' + (l.elevation_gain_m | number: '1.0-0') + ' m' : '—' }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    }
  `,
  imports: [DecimalPipe],
})
export class RunSplitsTableComponent {
  @Input() splits: ActivitySplit[] = [];
  @Input() laps: ActivityLap[] = [];

  readonly clock = clockLabel;
  readonly pace = paceLabel;

  /** Full kilometres are numbered; a shorter last split shows its distance. */
  splitLabel(split: ActivitySplit): string {
    return split.distance_m >= 1000 ? String(split.index) : (split.distance_m / 1000).toFixed(2);
  }

  elevation(change: number | null): string {
    if (change == null) return '—';
    const rounded = Math.round(change);
    return `${rounded > 0 ? '+' : ''}${rounded} m`;
  }

  lapPace(lap: ActivityLap): number | null {
    return lap.distance_m > 0 ? lap.duration_s / (lap.distance_m / 1000) : null;
  }
}
