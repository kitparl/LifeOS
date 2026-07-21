import {
  Component,
  EventEmitter,
  HostListener,
  Input,
  Output,
  computed,
  forwardRef,
  signal,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

/**
 * TypeSelectComponent — reusable "pick an existing value or create a new one"
 * combobox. Backs an extensible taxonomy (e.g. Q&A Type) without hardcoding.
 *
 * Single-select, stores a string value (ControlValueAccessor). When the user
 * commits a value not already in `options`, `(created)` fires so the parent can
 * persist it and make it reusable.
 *
 *   <app-type-select formControlName="type" [options]="types()" (created)="addType($event)" />
 */
@Component({
  selector: 'app-type-select',
  standalone: true,
  imports: [],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => TypeSelectComponent),
      multi: true,
    },
  ],
  template: `
    <div class="type-select">
      <div class="type-select__control" [class.type-select__control--open]="open()">
        <input
          class="type-select__input"
          [attr.placeholder]="placeholder"
          [value]="query()"
          [disabled]="disabled()"
          (focus)="open.set(true)"
          (input)="onQuery($event)"
          (keydown)="onKeydown($event)"
        />
        @if (value()) {
          <button type="button" class="type-select__clear" title="Clear" (click)="clear()">✕</button>
        }
        <button type="button" class="type-select__caret" (click)="toggle()" [disabled]="disabled()">▾</button>
      </div>

      @if (open()) {
        <div class="type-select__menu">
          @for (opt of filtered(); track opt) {
            <button
              type="button"
              class="type-select__option"
              [class.active]="opt === value()"
              (click)="select(opt)"
            >{{ opt }}</button>
          }
          @if (allowCreate && canCreate()) {
            <button type="button" class="type-select__option type-select__option--create" (click)="createNew()">
              + Create "{{ query() }}"
            </button>
          }
          @if (!filtered().length && !canCreate()) {
            <div class="type-select__empty">No matches</div>
          }
        </div>
      }
    </div>
  `,
})
export class TypeSelectComponent implements ControlValueAccessor {
  @Input() options: string[] = [];
  @Input() placeholder = 'Select or create…';
  @Input() allowCreate = true;

  @Output() created = new EventEmitter<string>();

  readonly value = signal('');
  readonly query = signal('');
  readonly open = signal(false);
  readonly disabled = signal(false);

  readonly filtered = computed(() => {
    const q = this.query().trim().toLowerCase();
    const opts = this.options ?? [];
    if (!q) return opts;
    return opts.filter((o) => o.toLowerCase().includes(q));
  });

  readonly canCreate = computed(() => {
    const q = this.query().trim();
    if (!q) return false;
    return !(this.options ?? []).some((o) => o.toLowerCase() === q.toLowerCase());
  });

  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  writeValue(value: string): void {
    this.value.set(value || '');
    this.query.set(value || '');
  }
  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }
  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
  setDisabledState(isDisabled: boolean): void {
    this.disabled.set(isDisabled);
  }

  @HostListener('document:click', ['$event'])
  onDocClick(event: MouseEvent): void {
    if (!(event.target as HTMLElement).closest('app-type-select')) {
      this.open.set(false);
      this.syncQueryToValue();
    }
  }

  onQuery(event: Event): void {
    this.query.set((event.target as HTMLInputElement).value);
    this.open.set(true);
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      event.preventDefault();
      const match = this.filtered()[0];
      if (match) this.select(match);
      else if (this.allowCreate && this.canCreate()) this.createNew();
    } else if (event.key === 'Escape') {
      this.open.set(false);
      this.syncQueryToValue();
    }
  }

  toggle(): void {
    this.open.set(!this.open());
  }

  select(opt: string): void {
    this.value.set(opt);
    this.query.set(opt);
    this.open.set(false);
    this.onChange(opt);
    this.onTouched();
  }

  createNew(): void {
    const label = this.query().trim();
    if (!label) return;
    this.created.emit(label);
    this.select(label);
  }

  clear(): void {
    this.value.set('');
    this.query.set('');
    this.onChange('');
    this.onTouched();
  }

  private syncQueryToValue(): void {
    this.query.set(this.value());
  }
}
