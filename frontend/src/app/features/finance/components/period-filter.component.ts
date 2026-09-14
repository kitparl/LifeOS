import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { PeriodPreset, PeriodSelection } from '../models/finance.models';
import { PERIOD_OPTIONS, startOfMonthIso, todayIso } from '../utils/period';

/**
 * Period selector for the whole Finance module. Defaults to This Month and
 * never moves off it on its own, even when the month has no activity.
 */
@Component({
  selector: 'app-finance-period-filter',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="flex flex-wrap items-center gap-2">
      @for (option of periodOptions; track option.value) {
        <button
          type="button"
          class="text-xs"
          [class.btn-primary]="period.preset === option.value"
          [class.btn-secondary]="period.preset !== option.value"
          (click)="choose(option.value)"
        >
          {{ option.label }}
        </button>
      }

      @if (period.preset === 'custom') {
        <div class="flex flex-wrap items-center gap-2">
          <input
            class="input-field !w-auto text-xs"
            type="date"
            [ngModel]="customStart()"
            (ngModelChange)="setStart($event)"
          />
          <span class="text-xs" style="color: var(--text-muted)">to</span>
          <input
            class="input-field !w-auto text-xs"
            type="date"
            [ngModel]="customEnd()"
            (ngModelChange)="setEnd($event)"
          />
        </div>
      }
    </div>
  `,
})
export class PeriodFilterComponent {
  @Input({ required: true }) period!: PeriodSelection;
  @Output() readonly periodChange = new EventEmitter<PeriodSelection>();

  readonly periodOptions = PERIOD_OPTIONS;
  readonly customStart = signal(startOfMonthIso());
  readonly customEnd = signal(todayIso());

  choose(preset: PeriodPreset): void {
    if (preset === 'custom') {
      this.emitCustom();
      return;
    }
    this.periodChange.emit({ preset });
  }

  setStart(value: string): void {
    this.customStart.set(value);
    this.emitCustom();
  }

  setEnd(value: string): void {
    this.customEnd.set(value);
    this.emitCustom();
  }

  private emitCustom(): void {
    this.periodChange.emit({
      preset: 'custom',
      start: this.customStart(),
      end: this.customEnd(),
    });
  }
}
