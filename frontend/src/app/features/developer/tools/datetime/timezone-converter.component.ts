import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { DateTimeInputComponent } from '../../shared/date-time-input.component';
import { DevHistoryPanelComponent } from '../../shared/dev-history-panel.component';
import { DevHistoryService } from '../../shared/dev-history.service';
import { TIMEZONE_PRESETS, convertTimezone, listTimeZones } from './timezone.util';

const HISTORY_DEBOUNCE_MS = 900;

@Component({
  selector: 'app-timezone-converter-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent, DateTimeInputComponent, DevHistoryPanelComponent],
  template: `
    <app-dev-tool-shell
      toolId="timezone-converter"
      title="Timezone Converter"
      description="Convert a date and time between timezones, using the browser's timezone database."
      icon="globe"
    >
      <div class="flex flex-wrap gap-2 pb-4">
        @for (preset of presets; track preset.label) {
          <button type="button" class="badge" style="cursor: pointer; background: var(--surface-3); color: var(--text);" (click)="applyPreset(preset)">
            {{ preset.label }}
          </button>
        }
      </div>

      <div class="grid gap-3 pb-3 md:grid-cols-3">
        <div class="space-y-1 md:col-span-1">
          <label class="form-label">Date &amp; time</label>
          <app-date-time-input [value]="dateTimeLocal()" (valueChange)="onDateTimeChange($event)" />
        </div>
        <div class="space-y-1">
          <label class="form-label">From timezone</label>
          <select class="input-field" [ngModel]="fromZone()" (ngModelChange)="onFromZoneChange($event)">
            @for (z of zones; track z) {
              <option [value]="z">{{ z }}</option>
            }
          </select>
        </div>
        <div class="flex items-end gap-2">
          <div class="flex-1 space-y-1">
            <label class="form-label">To timezone</label>
            <select class="input-field" [ngModel]="toZone()" (ngModelChange)="onToZoneChange($event)">
              @for (z of zones; track z) {
                <option [value]="z">{{ z }}</option>
              }
            </select>
          </div>
          <button type="button" class="btn-secondary" title="Swap timezones" (click)="swapZones()">Swap</button>
        </div>
      </div>

      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      } @else {
        <div class="flex items-center gap-2">
          <input class="input-field font-mono text-sm" readonly [ngModel]="result()" />
          <app-copy-button [text]="result()" />
        </div>
      }

      <app-dev-history-panel toolId="timezone-converter" />
    </app-dev-tool-shell>
  `,
})
export class TimezoneConverterToolComponent implements OnInit, OnDestroy {
  private readonly historyService = inject(DevHistoryService);
  private historyTimer: ReturnType<typeof setTimeout> | undefined;

  readonly zones = listTimeZones();
  readonly presets = TIMEZONE_PRESETS;
  readonly dateTimeLocal = signal('');
  readonly fromZone = signal('UTC');
  readonly toZone = signal('UTC');

  readonly result = computed(() => {
    if (!this.dateTimeLocal()) return '';
    try {
      return convertTimezone(this.dateTimeLocal(), this.fromZone(), this.toZone());
    } catch {
      return '';
    }
  });

  readonly error = computed(() => {
    if (!this.dateTimeLocal()) return null;
    try {
      convertTimezone(this.dateTimeLocal(), this.fromZone(), this.toZone());
      return null;
    } catch (e) {
      return e instanceof Error ? e.message : String(e);
    }
  });

  ngOnInit(): void {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    this.fromZone.set(tz);
    const now = new Date();
    now.setSeconds(0, 0);
    this.dateTimeLocal.set(now.toISOString().slice(0, 16));
    this.scheduleHistoryRecord();
  }

  ngOnDestroy(): void {
    clearTimeout(this.historyTimer);
  }

  onDateTimeChange(value: string): void {
    this.dateTimeLocal.set(value);
    this.scheduleHistoryRecord();
  }

  onFromZoneChange(value: string): void {
    this.fromZone.set(value);
    this.scheduleHistoryRecord();
  }

  onToZoneChange(value: string): void {
    this.toZone.set(value);
    this.scheduleHistoryRecord();
  }

  applyPreset(preset: { from: string; to: string }): void {
    this.fromZone.set(preset.from);
    this.toZone.set(preset.to);
    this.scheduleHistoryRecord();
  }

  swapZones(): void {
    const from = this.fromZone();
    this.fromZone.set(this.toZone());
    this.toZone.set(from);
    this.scheduleHistoryRecord();
  }

  private scheduleHistoryRecord(): void {
    clearTimeout(this.historyTimer);
    this.historyTimer = setTimeout(() => {
      if (this.error() || !this.result()) return;
      const input = `${this.dateTimeLocal()} (${this.fromZone()} → ${this.toZone()})`;
      void this.historyService.addEntry('timezone-converter', input, this.result());
    }, HISTORY_DEBOUNCE_MS);
  }
}
