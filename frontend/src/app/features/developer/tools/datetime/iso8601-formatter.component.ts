import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { DateTimeInputComponent } from '../../shared/date-time-input.component';
import { DevHistoryPanelComponent } from '../../shared/dev-history-panel.component';
import { DevHistoryEntry, DevHistoryService } from '../../shared/dev-history.service';
import { extractWallClockParts } from '../../shared/datetime-parse.util';

const OFFSETS: number[] = [];
for (let m = -12 * 60; m <= 14 * 60; m += 30) OFFSETS.push(m);

const HISTORY_DEBOUNCE_MS = 900;

function formatOffset(minutes: number): string {
  if (minutes === 0) return 'Z';
  const sign = minutes >= 0 ? '+' : '-';
  const abs = Math.abs(minutes);
  return `${sign}${String(Math.floor(abs / 60)).padStart(2, '0')}:${String(abs % 60).padStart(2, '0')}`;
}

@Component({
  selector: 'app-iso8601-formatter-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent, DateTimeInputComponent, DevHistoryPanelComponent],
  template: `
    <app-dev-tool-shell
      toolId="iso8601-formatter"
      title="ISO 8601 Formatter"
      description="Format a date and time as ISO 8601 with any UTC offset."
      icon="calendar-clock"
    >
      <div class="flex flex-wrap items-end gap-3 pb-3">
        <div class="min-w-[260px] flex-1">
          <label class="form-label">Date &amp; time</label>
          <app-date-time-input [value]="localValue()" (valueChange)="setLocalValue($event)" />
        </div>
        <div>
          <label class="form-label">UTC offset</label>
          <select class="input-field w-auto" [ngModel]="offsetMinutes()" (ngModelChange)="setOffset(+$event)">
            @for (o of offsets; track o) {
              <option [ngValue]="o">{{ formatOffset(o) }}</option>
            }
          </select>
        </div>
        <app-copy-button [text]="output()" />
      </div>
      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      } @else {
        <input class="input-field font-mono text-sm" readonly [ngModel]="output()" />
      }

      <app-dev-history-panel toolId="iso8601-formatter" (reuse)="onReuse($event)" />
    </app-dev-tool-shell>
  `,
})
export class Iso8601FormatterToolComponent implements OnInit, OnDestroy {
  private readonly historyService = inject(DevHistoryService);
  private historyTimer: ReturnType<typeof setTimeout> | undefined;

  readonly offsets = OFFSETS;
  readonly localValue = signal('');
  readonly offsetMinutes = signal(0);

  readonly output = computed(() => {
    if (!this.localValue()) return '';
    try {
      return `${extractWallClockParts(this.localValue())}${formatOffset(this.offsetMinutes())}`;
    } catch {
      return '';
    }
  });

  readonly error = computed(() => {
    if (!this.localValue()) return null;
    try {
      extractWallClockParts(this.localValue());
      return null;
    } catch (e) {
      return e instanceof Error ? e.message : String(e);
    }
  });

  ngOnInit(): void {
    const now = new Date();
    now.setSeconds(0, 0);
    this.localValue.set(now.toISOString().slice(0, 16));
    this.scheduleHistoryRecord();
  }

  ngOnDestroy(): void {
    clearTimeout(this.historyTimer);
  }

  setLocalValue(value: string): void {
    this.localValue.set(value);
    this.scheduleHistoryRecord();
  }

  onReuse(entry: DevHistoryEntry): void {
    this.setLocalValue(entry.input);
  }

  setOffset(value: number): void {
    this.offsetMinutes.set(value);
    this.scheduleHistoryRecord();
  }

  formatOffset(minutes: number): string {
    return formatOffset(minutes);
  }

  private scheduleHistoryRecord(): void {
    clearTimeout(this.historyTimer);
    this.historyTimer = setTimeout(() => {
      if (this.error() || !this.output()) return;
      void this.historyService.addEntry('iso8601-formatter', this.localValue(), this.output());
    }, HISTORY_DEBOUNCE_MS);
  }
}
