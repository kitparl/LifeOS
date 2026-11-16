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
 * Single-select stores a string; with `[multiple]="true"` it stores a string[]
 * and renders picks as removable tags (ControlValueAccessor). When the user
 * commits a value not already in `options`, `(created)` fires so the parent can
 * persist it and make it reusable.
 *
 *   <app-type-select formControlName="type" [options]="types()" (created)="addType($event)" />
 *   <app-type-select formControlName="tags" [multiple]="true" [options]="tags()" (created)="addTag($event)" />
 */
type TypeSelectValue = string | string[];

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
      <div
        class="type-select__control"
        [class.type-select__control--open]="open()"
        [class.type-select__control--multi]="multiple"
      >
        @if (multiple) {
          @for (item of selected(); track item) {
            <span class="type-select__tag">
              {{ item }}
              <button
                type="button"
                class="type-select__tag-remove"
                [title]="'Remove ' + item"
                [disabled]="disabled()"
                (click)="toggleSelected(item)"
              >✕</button>
            </span>
          }
        }
        <input
          class="type-select__input"
          [attr.placeholder]="multiple && selected().length ? '' : placeholder"
          [value]="query()"
          [disabled]="disabled()"
          (focus)="open.set(true)"
          (input)="onQuery($event)"
          (keydown)="onKeydown($event)"
        />
        @if (value() || selected().length) {
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
              [class.active]="isActive(opt)"
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
  @Input() multiple = false;

  @Output() created = new EventEmitter<string>();

  readonly value = signal('');
  readonly selected = signal<string[]>([]);
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

  private onChange: (value: TypeSelectValue) => void = () => {};
  private onTouched: () => void = () => {};

  writeValue(value: TypeSelectValue | null): void {
    if (this.multiple) {
      this.selected.set(Array.isArray(value) ? [...value] : []);
      this.query.set('');
      return;
    }
    const single = typeof value === 'string' ? value : '';
    this.value.set(single);
    this.query.set(single);
  }
  registerOnChange(fn: (value: TypeSelectValue) => void): void {
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
    } else if (event.key === 'Backspace' && this.multiple && !this.query()) {
      const last = this.selected().at(-1);
      if (last) this.toggleSelected(last);
    } else if (event.key === 'Escape') {
      this.open.set(false);
      this.syncQueryToValue();
    }
  }

  toggle(): void {
    this.open.set(!this.open());
  }

  isActive(opt: string): boolean {
    return this.multiple ? this.selected().includes(opt) : opt === this.value();
  }

  select(opt: string): void {
    if (this.multiple) {
      this.toggleSelected(opt);
      this.query.set('');
      return;
    }
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

  toggleSelected(opt: string): void {
    const current = this.selected();
    const next = current.includes(opt) ? current.filter((o) => o !== opt) : [...current, opt];
    this.selected.set(next);
    this.onChange(next);
    this.onTouched();
  }

  clear(): void {
    this.value.set('');
    this.selected.set([]);
    this.query.set('');
    this.onChange(this.multiple ? [] : '');
    this.onTouched();
  }

  private syncQueryToValue(): void {
    this.query.set(this.multiple ? '' : this.value());
  }
}
