import { Component, computed, input, model, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideDynamicIcon } from '@lucide/angular';
import { InputField, parseJson } from '../models/dsa.models';

/** Text past this length gets a taller box. */
const LONG_FIELD_CHARS = 80;

/**
 * Run test cases: one tab per case, one JSON box per input field. The parent owns the cases
 * (`casesChange` emits the whole edited list) so it can seed, persist and append to them.
 */
@Component({
  selector: 'app-dsa-test-cases',
  standalone: true,
  imports: [FormsModule, LucideDynamicIcon],
  template: `
    @let list = cases();
    <div class="space-y-3" data-testid="dsa-test-cases">
      <div class="flex flex-wrap items-center gap-1.5">
        @for (texts of list; track $index) {
          <button type="button" class="chip" [attr.aria-pressed]="$index === current()" [attr.data-testid]="'dsa-case-tab-' + $index"
            [style.border-color]="$index === current() ? 'var(--primary)' : null"
            [style.color]="$index === current() ? 'var(--primary-hover)' : null"
            (click)="selected.set($index)">
            Case {{ $index + 1 }}
            @if (invalid()[$index]) {
              <span style="color: var(--danger)" title="Has invalid JSON">•</span>
            }
          </button>
        }
        @if (list.length < max()) {
          <button type="button" class="btn-ghost !min-h-7 !px-1.5 text-xs" data-testid="dsa-case-add-button"
            title="Add a copy of this case" aria-label="Add test case" (click)="add()">
            <svg class="h-3.5 w-3.5" lucideIcon="plus" aria-hidden="true"></svg>
          </button>
        }
        <div class="ml-auto flex items-center gap-1">
          @if (list.length > 1) {
            <button type="button" class="btn-ghost !min-h-7 !px-2 text-xs" data-testid="dsa-case-remove-button" (click)="remove()">
              <svg class="h-3.5 w-3.5" lucideIcon="trash-2" aria-hidden="true"></svg>
              Delete case
            </button>
          }
          <button type="button" class="btn-ghost !min-h-7 !px-2 text-xs" data-testid="dsa-case-reset-button" (click)="resetToExamples.emit()">
            <svg class="h-3.5 w-3.5" lucideIcon="rotate-ccw" aria-hidden="true"></svg>
            Reset to examples
          </button>
        </div>
      </div>

      @if (list[current()]; as texts) {
        @for (field of fields(); track field.name; let f = $index) {
          <div class="space-y-1">
            <label class="block text-xs" [for]="'dsa-case-field-' + f">
              <span class="font-mono font-medium">{{ field.name }}</span>
              <span class="ml-1" style="color: var(--text-faint)">{{ field.type }}</span>
            </label>
            <textarea class="input-field font-mono text-xs" spellcheck="false" [id]="'dsa-case-field-' + f"
              [attr.data-testid]="'dsa-case-field-' + field.name" [rows]="texts[f].length > longField ? 4 : 1"
              [attr.aria-invalid]="!isJson(texts[f])" [ngModel]="texts[f]" (ngModelChange)="edit(f, $event)"></textarea>
            @if (!isJson(texts[f])) {
              <p class="text-xs" style="color: var(--danger)">Enter a JSON value, e.g. <code>[1,2,3]</code>, <code>5</code> or <code>"abc"</code>.</p>
            }
          </div>
        }
      }
    </div>
  `,
})
export class TestCasesComponent {
  readonly fields = input.required<InputField[]>();
  /** Per case, one JSON text per field. */
  readonly cases = input.required<string[][]>();
  readonly max = input.required<number>();
  /** Index of the case being edited. */
  readonly selected = model(0);
  readonly casesChange = output<string[][]>();
  readonly resetToExamples = output<void>();

  readonly longField = LONG_FIELD_CHARS;
  readonly current = computed(() => Math.min(this.selected(), Math.max(this.cases().length - 1, 0)));
  readonly invalid = computed(() => this.cases().map((texts) => texts.some((t) => !this.isJson(t))));

  isJson(text: string): boolean {
    return parseJson(text) !== undefined;
  }

  /** Adds a copy of the current case, the usual starting point for a new one. */
  add(): void {
    const list = this.cases();
    this.casesChange.emit([...list, [...(list[this.current()] ?? this.fields().map(() => ''))]]);
    this.selected.set(list.length);
  }

  remove(): void {
    const index = this.current();
    this.casesChange.emit(this.cases().filter((_, i) => i !== index));
    this.selected.set(Math.max(index - 1, 0));
  }

  edit(field: number, text: string): void {
    const index = this.current();
    this.casesChange.emit(
      this.cases().map((texts, i) => (i === index ? texts.map((t, f) => (f === field ? text : t)) : texts)),
    );
  }
}
