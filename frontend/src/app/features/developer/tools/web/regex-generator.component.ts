import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { REGEX_PRESETS, RegexPreset } from './regex-presets.util';

@Component({
  selector: 'app-regex-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="regex-generator"
      title="Regex Generator"
      description="Build a regular expression from common patterns."
      icon="regex"
    >
      <div class="grid gap-3 pb-4 sm:grid-cols-2 lg:grid-cols-3">
        @for (preset of presets; track preset.id) {
          <button
            type="button"
            class="panel panel--flat text-left"
            [style.border-color]="selected()?.id === preset.id ? 'var(--primary)' : 'var(--border)'"
            (click)="select(preset)"
          >
            <p class="text-sm font-semibold">{{ preset.label }}</p>
            <p class="text-xs text-[var(--text-muted)]">{{ preset.description }}</p>
          </button>
        }
      </div>

      @if (selected()) {
        <div class="flex items-center gap-2 pb-3">
          <input class="input-field font-mono text-sm" readonly [ngModel]="expression()" />
          <app-copy-button [text]="expression()" />
        </div>
        <div class="space-y-1">
          <label class="form-label">Try it</label>
          <input class="input-field font-mono text-sm" [ngModel]="testValue()" (ngModelChange)="setTestValue($event)" placeholder="Type a value to test…" />
          @if (testValue()) {
            <p class="text-sm" [style.color]="isMatch() ? 'var(--success)' : 'var(--danger)'">
              {{ isMatch() ? 'Matches' : 'Does not match' }}
            </p>
          }
        </div>
      } @else {
        <p class="text-sm text-[var(--text-muted)]">Choose a pattern above to generate its regular expression.</p>
      }
    </app-dev-tool-shell>
  `,
})
export class RegexGeneratorToolComponent {
  readonly presets = REGEX_PRESETS;
  readonly selected = signal<RegexPreset | null>(null);
  readonly testValue = signal('');

  readonly expression = computed(() => {
    const p = this.selected();
    return p ? `/${p.pattern}/${p.flags}` : '';
  });

  readonly isMatch = computed(() => {
    const p = this.selected();
    if (!p || !this.testValue()) return false;
    try {
      return new RegExp(p.pattern, p.flags).test(this.testValue());
    } catch {
      return false;
    }
  });

  select(preset: RegexPreset): void {
    this.selected.set(preset);
  }

  setTestValue(value: string): void {
    this.testValue.set(value);
  }
}
