import {
  Component,
  EventEmitter,
  Input,
  Output,
  forwardRef,
  signal,
} from '@angular/core';
import { ControlValueAccessor, FormsModule, NG_VALUE_ACCESSOR } from '@angular/forms';

/**
 * DateChipsComponent — pick ISO dates into a removable chip list.
 *
 *   <app-date-chips formControlName="skip_dates" />
 *   <app-date-chips [(ngModel)]="skipDates" />
 */
@Component({
  selector: 'app-date-chips',
  standalone: true,
  imports: [FormsModule],
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
      <div class="flex gap-2 items-end">
        <input
          class="input-field flex-1"
          type="date"
          [disabled]="disabled()"
          [(ngModel)]="draft"
          [ngModelOptions]="{ standalone: true }"
        />
        <button
          type="button"
          class="btn-primary text-xs shrink-0"
          [disabled]="disabled() || !draft"
          (click)="add()"
        >
          Add
        </button>
      </div>
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
  @Input() placeholder = 'Add a date';
  @Output() changed = new EventEmitter<string[]>();

  readonly dates = signal<string[]>([]);
  readonly disabled = signal(false);
  draft = '';

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

  add(): void {
    const d = (this.draft || '').trim();
    if (!d) return;
    const next = Array.from(new Set([...this.dates(), d])).sort();
    this.dates.set(next);
    this.draft = '';
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
