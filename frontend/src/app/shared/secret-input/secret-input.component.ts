import {
  Component,
  Input,
  forwardRef,
  signal,
} from '@angular/core';
import { ControlValueAccessor, FormsModule, NG_VALUE_ACCESSOR } from '@angular/forms';

/**
 * SecretInputComponent — masked text input with an eye toggle to reveal/hide.
 * Compatible with ReactiveForms (formControlName) and ngModel.
 *
 *   <app-secret-input formControlName="password" placeholder="••••••••" />
 *   <app-secret-input [(ngModel)]="botToken" />
 */
@Component({
  selector: 'app-secret-input',
  standalone: true,
  imports: [FormsModule],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => SecretInputComponent),
      multi: true,
    },
  ],
  template: `
    <div class="secret-input">
      <input
        class="input-field secret-input__field"
        [attr.id]="inputId || null"
        [type]="revealed() ? 'text' : 'password'"
        [attr.autocomplete]="autocomplete"
        [placeholder]="placeholder"
        [disabled]="disabled()"
        [value]="value()"
        (input)="onInput($event)"
        (blur)="onTouched()"
      />
      <button
        type="button"
        class="secret-input__toggle btn-ghost !px-2"
        [attr.title]="revealed() ? 'Hide' : 'Show'"
        [attr.aria-label]="revealed() ? 'Hide value' : 'Show value'"
        [disabled]="disabled()"
        (click)="toggle()"
      >
        {{ revealed() ? '🙈' : '👁' }}
      </button>
    </div>
  `,
  styles: [
    `
      .secret-input {
        display: flex;
        align-items: stretch;
        gap: 0.25rem;
        width: 100%;
      }
      .secret-input__field {
        flex: 1;
        min-width: 0;
      }
      .secret-input__toggle {
        flex-shrink: 0;
        font-size: 0.875rem;
        line-height: 1;
        color: var(--text-muted);
      }
    `,
  ],
})
export class SecretInputComponent implements ControlValueAccessor {
  @Input() placeholder = '';
  @Input() autocomplete = 'off';
  @Input() inputId = '';

  readonly value = signal('');
  readonly revealed = signal(false);
  readonly disabled = signal(false);

  private onChange: (value: string) => void = () => {};
  onTouched: () => void = () => {};

  writeValue(value: string | null): void {
    this.value.set(value ?? '');
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

  onInput(event: Event): void {
    const next = (event.target as HTMLInputElement).value;
    this.value.set(next);
    this.onChange(next);
  }

  toggle(): void {
    this.revealed.update((v) => !v);
  }
}
