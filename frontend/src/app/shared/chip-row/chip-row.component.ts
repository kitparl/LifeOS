import { Component, input, output } from '@angular/core';

export interface ChipOption<T extends string = string> {
  id: T;
  label: string;
}

/** Single-select chip row (filters such as countries, categories, difficulty). */
@Component({
  selector: 'app-chip-row',
  standalone: true,
  template: `
    <div class="flex gap-1.5 overflow-x-auto pb-1" role="group" [attr.aria-label]="label()">
      @for (o of options(); track o.id) {
        <button
          type="button"
          class="chip shrink-0 cursor-pointer"
          [style.background]="o.id === selected() ? 'var(--primary-soft)' : null"
          [style.border-color]="o.id === selected() ? 'var(--primary)' : null"
          [style.color]="o.id === selected() ? 'var(--primary-hover)' : null"
          [attr.aria-pressed]="o.id === selected()"
          [attr.data-testid]="testIdPrefix() + '-' + (o.id || 'all')"
          (click)="selectedChange.emit(o.id)"
        >
          {{ o.label }}
        </button>
      }
    </div>
  `,
})
export class ChipRowComponent {
  readonly label = input.required<string>();
  readonly options = input.required<readonly ChipOption[]>();
  readonly selected = input.required<string>();
  /** data-testid prefix per chip: `<prefix>-<option id>` (`-all` for the empty id). */
  readonly testIdPrefix = input('chip');
  readonly selectedChange = output<string>();
}
