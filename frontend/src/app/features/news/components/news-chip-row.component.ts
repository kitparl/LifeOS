import { Component, input, output } from '@angular/core';
import { NewsOption } from '../models/news.models';

/** Single-select chip row (countries, categories, saved filters). */
@Component({
  selector: 'app-news-chip-row',
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
          [attr.data-testid]="'news-chip-' + (o.id || 'all')"
          (click)="selectedChange.emit(o.id)"
        >
          {{ o.label }}
        </button>
      }
    </div>
  `,
})
export class NewsChipRowComponent {
  readonly label = input.required<string>();
  readonly options = input.required<readonly NewsOption[]>();
  readonly selected = input.required<string>();
  readonly selectedChange = output<string>();
}
