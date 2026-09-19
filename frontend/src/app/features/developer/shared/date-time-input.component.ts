import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { toDatetimeLocalValue } from './datetime-parse.util';

/**
 * A date/time input that supports free typing and pasting (any format `Date` or
 * `extractWallClockParts` can parse) alongside a native picker for easy selection —
 * the two stay in sync through the same `value`/`valueChange`.
 */
@Component({
  selector: 'app-date-time-input',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="flex gap-2">
      <input
        class="input-field flex-1 font-mono text-sm"
        type="text"
        [placeholder]="placeholder"
        [ngModel]="value"
        (ngModelChange)="valueChange.emit($event)"
      />
      <input
        class="input-field w-auto"
        type="datetime-local"
        title="Pick a date and time"
        [ngModel]="pickerValue()"
        (ngModelChange)="valueChange.emit($event)"
      />
    </div>
  `,
})
export class DateTimeInputComponent {
  @Input() value = '';
  @Input() placeholder = 'Type, paste, or pick a date & time…';
  @Output() readonly valueChange = new EventEmitter<string>();

  pickerValue(): string {
    if (!this.value) return '';
    const d = new Date(this.value);
    return isNaN(d.getTime()) ? '' : toDatetimeLocalValue(d);
  }
}
