import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  computed,
  effect,
  forwardRef,
  input,
  output,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import flatpickr from 'flatpickr';
import monthSelectPlugin from 'flatpickr/dist/plugins/monthSelect';
import type { Instance } from 'flatpickr/dist/types/instance';
import type { Options } from 'flatpickr/dist/types/options';
import { ensureStylesheet } from '../../core/utils/stylesheet';
import {
  DateInputMode,
  QUICK_PICKS,
  dateToValue,
  displayDate,
  outOfRange,
  parseTyped,
  roundToMinutes,
  startOfDay,
  stepDate,
  valueToDate,
} from './date-input.utils';

const PLACEHOLDERS: Record<DateInputMode, string> = {
  date: 'Pick or type, e.g. tomorrow',
  datetime: 'Pick or type, e.g. fri 5pm',
  time: 'Pick or type, e.g. 5:30pm',
  month: 'Pick a month',
};

const HINT = 'Type “tomorrow”, “next fri”, “25 dec” · t ⏎ = today · + / − and PgUp / PgDn to nudge';

const STEP_KEYS: Record<string, ['small' | 'large', 1 | -1]> = {
  '+': ['small', 1],
  '=': ['small', 1],
  '-': ['small', -1],
  PageUp: ['large', 1],
  PageDown: ['large', -1],
};

/**
 * The app's one date / time / month field (flatpickr calendar + plain-English typing).
 *
 * Stores the same strings the native inputs did — `YYYY-MM-DD`, `YYYY-MM-DDTHH:mm`, `HH:mm`,
 * `YYYY-MM` — and `''` when cleared, so forms and the API are unchanged. Works with
 * `formControlName`, `[(ngModel)]`, or `[value]` + `(valueChange)`.
 *
 *   <app-date-input formControlName="due_date" inputId="task-due" />
 *   <app-date-input mode="time" [(ngModel)]="time" />
 *   <app-date-input mode="datetime" [value]="start" (valueChange)="start = $event" [min]="today" />
 */
@Component({
  selector: 'app-date-input',
  standalone: true,
  host: { class: 'block min-w-0' },
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => DateInputComponent), multi: true }],
  template: `
    <div class="relative">
      <input
        #field
        type="text"
        [class]="inputClass() + ' w-full' + (clearable() ? ' pr-8' : '')"
        autocomplete="off"
        spellcheck="false"
        enterkeyhint="done"
        [attr.id]="inputId() || null"
        [attr.name]="name() || null"
        [attr.data-testid]="testId() || null"
        [attr.aria-label]="ariaLabel() || null"
        [attr.title]="hint"
        [placeholder]="placeholder() || placeholders[mode()]"
        [disabled]="isDisabled()"
        (keydown)="onKeydown($event)"
        (blur)="markTouched()"
      />
      @if (current() && clearable() && !isDisabled()) {
        <button
          type="button"
          class="date-input__clear"
          aria-label="Clear"
          tabindex="-1"
          (mousedown)="$event.preventDefault()"
          (click)="clear()"
        >✕</button>
      }
    </div>
  `,
  styles: [
    `
      .date-input__clear {
        position: absolute;
        top: 50%;
        right: 0.4rem;
        transform: translateY(-50%);
        padding: 0.15rem 0.3rem;
        border: none;
        background: transparent;
        color: var(--text-muted);
        font-size: 0.7rem;
        line-height: 1;
        cursor: pointer;
      }
      .date-input__clear:hover {
        color: var(--danger);
      }
    `,
  ],
})
export class DateInputComponent implements ControlValueAccessor, AfterViewInit, OnDestroy {
  readonly mode = input<DateInputMode>('date');
  /** Earliest / latest allowed, as stored strings of the same mode (time mode ignores them). */
  readonly min = input<string | null | undefined>('');
  readonly max = input<string | null | undefined>('');
  readonly placeholder = input('');
  readonly inputId = input('');
  readonly name = input('');
  readonly testId = input('');
  readonly ariaLabel = input('');
  readonly clearable = input(true);
  /** Field styling; the default matches every other form field. */
  readonly inputClass = input('input-field');
  /** For use without forms; `undefined` leaves the value to the form control. */
  readonly value = input<string | null | undefined>(undefined);
  /** Shown greyed out and not editable, while a form control keeps (and submits) its value. */
  readonly readonly = input(false);

  /** Emits the stored string whenever the person picks, types or clears a value. */
  readonly valueChange = output<string>();

  readonly placeholders = PLACEHOLDERS;
  readonly hint = HINT;
  readonly current = signal('');
  private readonly formDisabled = signal(false);
  readonly isDisabled = computed(() => this.readonly() || this.formDisabled());

  private readonly field = viewChild.required<ElementRef<HTMLInputElement>>('field');
  private picker: Instance | null = null;
  private builtFor = '';
  /**
   * Non-empty text flatpickr is about to read. If it then reports no date (unreadable, or outside
   * min/max), the stored value is restored instead of being cleared.
   */
  private pendingText = '';

  private onChange: (value: string) => void = () => undefined;
  private onTouched: () => void = () => undefined;

  constructor() {
    effect(() => {
      const value = this.value();
      if (value !== undefined) untracked(() => this.writeValue(value));
    });
    effect(() => {
      this.mode();
      this.min();
      this.max();
      untracked(() => this.build());
    });
  }

  ngAfterViewInit(): void {
    this.build();
  }

  ngOnDestroy(): void {
    this.picker?.destroy();
    this.picker = null;
  }

  // ------------------------------------------------------------------
  // ControlValueAccessor
  // ------------------------------------------------------------------

  writeValue(value: string | null | undefined): void {
    this.current.set(value ?? '');
    this.syncPicker();
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.formDisabled.set(isDisabled);
  }

  markTouched(): void {
    this.onTouched();
  }

  // ------------------------------------------------------------------
  // Interaction
  // ------------------------------------------------------------------

  clear(): void {
    this.commit('');
    this.picker?.clear(false);
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape' && this.picker?.isOpen) {
      // Close only the calendar, not a modal around it.
      event.stopPropagation();
      this.picker.close();
      return;
    }
    const step = STEP_KEYS[event.key];
    if (!step || event.ctrlKey || event.metaKey || event.altKey || !this.picker) return;
    const text = this.field().nativeElement.value.trim();
    const currentDate = this.currentDate();
    // Only nudge an untouched field: "-" is also typed inside "2026-11-13".
    if (text && !(currentDate && text === displayDate(currentDate, this.mode()))) return;
    event.preventDefault();
    const next = stepDate(currentDate ?? this.startingPoint(), this.mode(), step[0], step[1]);
    if (!outOfRange(next, this.mode(), this.min() ?? '', this.max() ?? '')) this.picker.setDate(next, true);
  }

  // ------------------------------------------------------------------
  // flatpickr
  // ------------------------------------------------------------------

  private build(): void {
    const element = this.field()?.nativeElement;
    const mode = this.mode();
    const key = `${mode}|${this.min() ?? ''}|${this.max() ?? ''}`;
    if (!element || (this.picker && key === this.builtFor)) return;
    this.picker?.destroy();
    ensureStylesheet('flatpickr-css', 'flatpickr/flatpickr.min.css');
    if (mode === 'month') ensureStylesheet('flatpickr-month-css', 'flatpickr/month-select/style.css');

    const bound = (value: string | null | undefined): Date | undefined =>
      mode === 'time' ? undefined : (valueToDate(value, mode) ?? undefined);
    const options: Partial<Options> = {
      allowInput: true,
      disableMobile: true,
      enableTime: mode === 'datetime' || mode === 'time',
      noCalendar: mode === 'time',
      minuteIncrement: 5,
      minDate: bound(this.min()),
      maxDate: bound(this.max()),
      plugins: mode === 'month' ? [monthSelectPlugin({ shorthand: true })] : [],
      formatDate: (date: Date) => displayDate(date, mode),
      parseDate: (text: string) => this.parse(text) as Date,
      errorHandler: () => undefined,
      onChange: (dates: Date[]) => this.onPicked(dates[0] ?? null),
      onReady: (_dates: Date[], _text: string, instance: Instance) => this.addFooter(instance),
    };
    this.picker = flatpickr(element, options) as Instance;
    this.builtFor = key;
    this.syncPicker();
  }

  /**
   * Shows the stored value in the field and calendar without emitting a change. A saved value
   * outside min/max (old data) is still shown as text — flatpickr would otherwise drop it.
   */
  private syncPicker(): void {
    if (!this.picker) return;
    const date = this.currentDate();
    if (date && !outOfRange(date, this.mode(), this.min() ?? '', this.max() ?? '')) {
      this.picker.setDate(date, false);
      return;
    }
    this.picker.clear(false);
    if (date) this.field().nativeElement.value = displayDate(date, this.mode());
  }

  private parse(text: string): Date | null {
    const currentDate = this.currentDate();
    this.pendingText = text.trim();
    if (currentDate && this.pendingText === displayDate(currentDate, this.mode())) return currentDate;
    return parseTyped(text, this.mode(), currentDate);
  }

  private onPicked(date: Date | null): void {
    const typed = this.pendingText;
    this.pendingText = '';
    if (!date && typed) {
      this.syncPicker();
      return;
    }
    this.commit(date ? dateToValue(date, this.mode()) : '');
  }

  private commit(value: string): void {
    if (value === this.current()) return;
    this.current.set(value);
    this.onChange(value);
    this.valueChange.emit(value);
  }

  private addFooter(instance: Instance): void {
    const mode = this.mode();
    const footer = document.createElement('div');
    footer.className = 'date-input__footer';
    const buttons = document.createElement('div');
    buttons.className = 'date-input__picks';
    for (const pick of QUICK_PICKS[mode]) {
      buttons.appendChild(
        this.footerButton(pick.label, () => {
          const date = pick.value(new Date(), this.currentDate());
          if (outOfRange(date, mode, this.min() ?? '', this.max() ?? '')) return;
          instance.setDate(date, true);
          instance.close();
        }),
      );
    }
    if (this.clearable()) {
      buttons.appendChild(
        this.footerButton('Clear', () => {
          this.clear();
          instance.close();
        }),
      );
    }
    footer.appendChild(buttons);
    if (mode !== 'month') {
      const hint = document.createElement('p');
      hint.className = 'date-input__hint';
      hint.textContent = HINT;
      footer.appendChild(hint);
    }
    instance.calendarContainer.appendChild(footer);
  }

  private footerButton(label: string, onClick: () => void): HTMLButtonElement {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'date-input__pick';
    button.textContent = label;
    button.addEventListener('click', onClick);
    return button;
  }

  private currentDate(): Date | null {
    return valueToDate(this.current(), this.mode());
  }

  /** Where `+` / `-` start from on an empty field. */
  private startingPoint(): Date {
    const now = new Date();
    if (this.mode() === 'date') return startOfDay(now);
    if (this.mode() === 'month') return new Date(now.getFullYear(), now.getMonth(), 1);
    return roundToMinutes(now, 5);
  }
}
