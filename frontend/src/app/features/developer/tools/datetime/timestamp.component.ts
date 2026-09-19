import { Component, OnDestroy, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { DateTimeInputComponent } from '../../shared/date-time-input.component';
import { DevHistoryPanelComponent } from '../../shared/dev-history-panel.component';
import { DevHistoryService } from '../../shared/dev-history.service';

const HISTORY_DEBOUNCE_MS = 900;

@Component({
  selector: 'app-timestamp-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent, DateTimeInputComponent, DevHistoryPanelComponent],
  template: `
    <app-dev-tool-shell
      toolId="timestamp"
      title="Unix Timestamp ↔ Date Converter"
      description="Convert between Unix timestamps and human-readable dates."
      icon="clock"
    >
      <div class="flex flex-wrap items-end justify-between gap-3 pb-3">
        <div class="inline-flex overflow-hidden rounded-[var(--radius-sm)] border border-[var(--border)]">
          <button type="button" class="px-3 py-1.5 text-sm" [style.background]="unit() === 's' ? 'var(--primary)' : 'transparent'" [style.color]="unit() === 's' ? '#fff' : 'var(--text)'" (click)="setUnit('s')">Seconds</button>
          <button type="button" class="px-3 py-1.5 text-sm border-l border-[var(--border)]" [style.background]="unit() === 'ms' ? 'var(--primary)' : 'transparent'" [style.color]="unit() === 'ms' ? '#fff' : 'var(--text)'" (click)="setUnit('ms')">Milliseconds</button>
        </div>
        <button type="button" class="btn-secondary" (click)="now()">Now</button>
      </div>
      @if (error()) {
        <p class="pb-2 text-sm text-[var(--danger)]">{{ error() }}</p>
      }
      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">Unix timestamp ({{ unit() }})</label>
          <div class="flex gap-2">
            <input class="input-field font-mono text-sm" [ngModel]="timestamp()" (ngModelChange)="onTimestampChange($event)" />
            <app-copy-button [text]="timestamp()" />
          </div>
        </div>
        <div class="space-y-1">
          <label class="form-label">Date / time</label>
          <div class="flex gap-2">
            <app-date-time-input class="flex-1" [value]="dateText()" (valueChange)="onDateChange($event)" placeholder="e.g. 2026-01-15T10:30:00Z" />
            <app-copy-button [text]="dateText()" />
          </div>
        </div>
      </div>

      <app-dev-history-panel toolId="timestamp" />
    </app-dev-tool-shell>
  `,
})
export class TimestampToolComponent implements OnDestroy {
  private readonly historyService = inject(DevHistoryService);
  private historyTimer: ReturnType<typeof setTimeout> | undefined;

  readonly unit = signal<'s' | 'ms'>('s');
  readonly timestamp = signal('');
  readonly dateText = signal('');
  readonly error = signal<string | null>(null);

  ngOnDestroy(): void {
    clearTimeout(this.historyTimer);
  }

  setUnit(u: 's' | 'ms'): void {
    this.unit.set(u);
    if (this.timestamp()) this.onTimestampChange(this.timestamp());
  }

  onTimestampChange(value: string): void {
    this.timestamp.set(value);
    if (!value.trim()) {
      this.dateText.set('');
      this.error.set(null);
      return;
    }
    const num = Number(value);
    if (!Number.isFinite(num)) {
      this.error.set('Enter a numeric Unix timestamp.');
      return;
    }
    const ms = this.unit() === 's' ? num * 1000 : num;
    const d = new Date(ms);
    if (isNaN(d.getTime())) {
      this.error.set('Timestamp is out of range.');
      return;
    }
    this.dateText.set(d.toISOString());
    this.error.set(null);
    this.scheduleHistoryRecord();
  }

  onDateChange(value: string): void {
    this.dateText.set(value);
    if (!value.trim()) {
      this.timestamp.set('');
      this.error.set(null);
      return;
    }
    const d = new Date(value);
    if (isNaN(d.getTime())) {
      this.error.set('Could not parse that date/time — try ISO 8601 format.');
      return;
    }
    const ms = d.getTime();
    this.timestamp.set(String(this.unit() === 's' ? Math.floor(ms / 1000) : ms));
    this.error.set(null);
    this.scheduleHistoryRecord();
  }

  now(): void {
    const nowMs = Date.now();
    this.onTimestampChange(String(this.unit() === 's' ? Math.floor(nowMs / 1000) : nowMs));
  }

  private scheduleHistoryRecord(): void {
    clearTimeout(this.historyTimer);
    this.historyTimer = setTimeout(() => {
      if (this.error() || !this.timestamp() || !this.dateText()) return;
      void this.historyService.addEntry('timestamp', this.timestamp(), this.dateText());
    }, HISTORY_DEBOUNCE_MS);
  }
}
