import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { RunningStats } from '../models/running.models';

@Component({
  selector: 'app-running-shoes-tab',
  standalone: true,
  imports: [DatePipe],
  host: { class: 'contents' },
  template: `
    @if (stats?.shoe_totals?.length) {
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Distance by shoe</div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr>
                <th class="px-3 py-2 text-left">Shoe</th>
                <th class="px-3 py-2 text-left">Km</th>
                <th class="px-3 py-2 text-left">Runs</th>
                <th class="px-3 py-2 text-left">Last run</th>
              </tr>
            </thead>
            <tbody>
              @for (s of stats!.shoe_totals; track s.shoe) {
                <tr style="border-bottom: 1px solid var(--border)">
                  <td class="px-3 py-2">
                    <button type="button" class="link text-sm" (click)="filterByShoe.emit(s.shoe)">{{ s.shoe }}</button>
                  </td>
                  <td class="px-3 py-2">{{ s.total_km }} km</td>
                  <td class="px-3 py-2">{{ s.run_count }}</td>
                  <td class="px-3 py-2 text-xs" style="color: var(--text-muted)">
                    {{ s.last_run_date ? (s.last_run_date | date: 'mediumDate') : '—' }}
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    } @else {
      <div class="panel">
        <p class="text-sm" style="color: var(--text-muted)">No shoe distance yet. Log a run or event with shoes selected.</p>
      </div>
    }
  `,
})
export class RunningShoesTabComponent {
  @Input() stats: RunningStats | null = null;
  @Output() readonly filterByShoe = new EventEmitter<string>();
}
