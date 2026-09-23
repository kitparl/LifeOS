import { Component, OnDestroy, computed, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { DateTimeInputComponent } from '../../shared/date-time-input.component';
import { DevHistoryPanelComponent } from '../../shared/dev-history-panel.component';
import { DevHistoryEntry, DevHistoryService } from '../../shared/dev-history.service';

const HISTORY_DEBOUNCE_MS = 900;
/** Separates the two dates in a recorded entry's `input` — see scheduleHistoryRecord/onReuse. */
const RANGE_SEPARATOR = ' → ';

@Component({
  selector: 'app-date-difference-tool',
  standalone: true,
  imports: [DevToolShellComponent, DecimalPipe, DateTimeInputComponent, DevHistoryPanelComponent],
  template: `
    <app-dev-tool-shell
      toolId="date-difference"
      title="Date Difference Calculator"
      description="Calculate the difference between two dates."
      icon="calendar-clock"
    >
      <div class="grid gap-3 pb-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">From</label>
          <app-date-time-input [value]="from()" (valueChange)="setFrom($event)" />
        </div>
        <div class="space-y-1">
          <label class="form-label">To</label>
          <app-date-time-input [value]="to()" (valueChange)="setTo($event)" />
        </div>
      </div>
      @if (result()) {
        <p class="text-lg font-semibold">{{ result()!.days }}d {{ result()!.hours }}h {{ result()!.minutes }}m {{ result()!.seconds }}s</p>
        <p class="text-sm text-[var(--text-muted)]">{{ result()!.totalSeconds | number }} total seconds</p>
      } @else {
        <p class="text-sm text-[var(--text-muted)]">Choose both dates to see the difference.</p>
      }

      <app-dev-history-panel toolId="date-difference" (reuse)="onReuse($event)" />
    </app-dev-tool-shell>
  `,
})
export class DateDifferenceToolComponent implements OnDestroy {
  private readonly historyService = inject(DevHistoryService);
  private historyTimer: ReturnType<typeof setTimeout> | undefined;

  readonly from = signal('');
  readonly to = signal('');

  readonly result = computed(() => {
    if (!this.from() || !this.to()) return null;
    const a = new Date(this.from()).getTime();
    const b = new Date(this.to()).getTime();
    if (isNaN(a) || isNaN(b)) return null;
    const totalSeconds = Math.floor(Math.abs(b - a) / 1000);
    return {
      totalSeconds,
      days: Math.floor(totalSeconds / 86400),
      hours: Math.floor((totalSeconds % 86400) / 3600),
      minutes: Math.floor((totalSeconds % 3600) / 60),
      seconds: totalSeconds % 60,
    };
  });

  ngOnDestroy(): void {
    clearTimeout(this.historyTimer);
  }

  setFrom(value: string): void {
    this.from.set(value);
    this.scheduleHistoryRecord();
  }

  setTo(value: string): void {
    this.to.set(value);
    this.scheduleHistoryRecord();
  }

  onReuse(entry: DevHistoryEntry): void {
    const separatorIndex = entry.input.indexOf(RANGE_SEPARATOR);
    if (separatorIndex === -1) return;
    this.from.set(entry.input.slice(0, separatorIndex));
    this.to.set(entry.input.slice(separatorIndex + RANGE_SEPARATOR.length));
    this.scheduleHistoryRecord();
  }

  private scheduleHistoryRecord(): void {
    clearTimeout(this.historyTimer);
    this.historyTimer = setTimeout(() => {
      const r = this.result();
      if (!r) return;
      void this.historyService.addEntry(
        'date-difference',
        `${this.from()}${RANGE_SEPARATOR}${this.to()}`,
        `${r.days}d ${r.hours}h ${r.minutes}m ${r.seconds}s`,
      );
    }, HISTORY_DEBOUNCE_MS);
  }
}
