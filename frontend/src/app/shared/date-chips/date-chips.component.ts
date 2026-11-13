import {
  Component,
  EventEmitter,
  Input,
  Output,
  forwardRef,
  signal,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { DateInputComponent } from '../date-input/date-input.component';

/**
 * DateChipsComponent — pick ISO dates into a removable chip list. Picking (or typing) a date adds it.
 *
 *   <app-date-chips formControlName="skip_dates" />
 *   <app-date-chips [(ngModel)]="skipDates" />
 */
@Component({
  selector: 'app-date-chips',
  standalone: true,
  imports: [DateInputComponent],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => DateChipsComponent),
      multi: true,
    },
  ],
  template: `
    <div class="date-chips">
      <div class="flex flex-wrap gap-1.5 mb-2">
        @for (d of dates(); track d) {
          <span class="chip">
            {{ d }}
            <button
              type="button"
              class="date-chips__remove"
              title="Remove"
              [disabled]="disabled()"
              (click)="remove(d)"
            >✕</button>
          </span>
        }
        @if (!dates().length) {
          <span class="text-xs" style="color: var(--text-muted)">No dates added</span>
        }
      </div>
      <app-date-input
        #picker
        ariaLabel="Add a date"
        [placeholder]="placeholder"
        [readonly]="disabled()"
        (valueChange)="add($event); picker.writeValue('')"
      />
    </div>
  `,
  styles: [
    `
      .date-chips__remove {
        border: none;
        background: transparent;
        cursor: pointer;
        padding: 0;
        margin-left: 0.15rem;
        color: var(--text-muted);
        font-size: 0.7rem;
        line-height: 1;
      }
      .date-chips__remove:hover {
        color: var(--danger, #c0392b);
      }
    `,
  ],
})
export class DateChipsComponent implements ControlValueAccessor {
  @Input() placeholder = 'Pick or type a date to add it';
  @Output() changed = new EventEmitter<string[]>();

  readonly dates = signal<string[]>([]);
  readonly disabled = signal(false);

  private onChange: (value: string[]) => void = () => {};
  private onTouched: () => void = () => {};

  writeValue(value: string[] | null): void {
    this.dates.set(Array.isArray(value) ? [...value].sort() : []);
  }

  registerOnChange(fn: (value: string[]) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled.set(isDisabled);
  }

  add(date: string): void {
    if (!date) return;
    const next = Array.from(new Set([...this.dates(), date])).sort();
    this.dates.set(next);
    this.emit(next);
  }

  remove(d: string): void {
    const next = this.dates().filter((x) => x !== d);
    this.dates.set(next);
    this.emit(next);
  }

  private emit(next: string[]): void {
    this.onChange(next);
    this.onTouched();
    this.changed.emit(next);
  }
}
