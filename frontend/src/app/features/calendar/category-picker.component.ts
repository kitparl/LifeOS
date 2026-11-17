import { Component, computed, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { categoryColor, categoryLabel, normalizeCategory } from './models/calendar.models';

/** Category chips with an "Other" option for adding a custom category. */
@Component({
  selector: 'app-category-picker',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="flex flex-wrap items-center gap-1.5">
      @for (cat of options(); track cat) {
        <button
          type="button"
          class="rounded-full px-2.5 py-0.5 text-xs font-medium border transition-all"
          [style.background]="value() === cat ? color(cat) : 'transparent'"
          [style.color]="value() === cat ? '#fff' : 'var(--text-muted)'"
          [style.border-color]="color(cat)"
          (click)="valueChange.emit(cat)"
        >
          {{ label(cat) }}
        </button>
      }
      @if (adding()) {
        <input
          type="text"
          class="input-field text-xs !w-32 !py-0.5"
          maxlength="32"
          placeholder="New category"
          [(ngModel)]="draft"
          [ngModelOptions]="{ standalone: true }"
          (keydown.enter)="confirm($event)"
          (keydown.escape)="cancel($event)"
          (blur)="confirm()"
          #draftInput
          autofocus
        />
      } @else {
        <button
          type="button"
          class="rounded-full px-2.5 py-0.5 text-xs font-medium border border-dashed"
          style="color: var(--text-muted); border-color: var(--text-muted)"
          (click)="adding.set(true)"
        >
          + Other
        </button>
      }
    </div>
  `,
})
export class CategoryPickerComponent {
  readonly categories = input.required<string[]>();
  readonly value = input.required<string>();
  readonly valueChange = output<string>();

  readonly adding = signal(false);
  draft = '';

  /** Known categories, plus the current value if it is not in the list yet (e.g. just typed). */
  readonly options = computed(() => {
    const list = this.categories();
    const current = this.value();
    return current && !list.includes(current) ? [...list, current] : list;
  });

  readonly color = categoryColor;
  readonly label = categoryLabel;

  confirm(event?: Event): void {
    event?.preventDefault();
    const name = normalizeCategory(this.draft);
    if (name) this.valueChange.emit(name);
    this.cancel();
  }

  cancel(event?: Event): void {
    event?.stopPropagation();
    this.draft = '';
    this.adding.set(false);
  }
}
