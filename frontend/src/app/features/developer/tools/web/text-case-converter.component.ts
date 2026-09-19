import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { convertAllCases } from './case-converter.util';

@Component({
  selector: 'app-text-case-converter-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="text-case-converter"
      title="Text Case Converter"
      description="Convert text into every common case style at once."
      icon="case-sensitive"
    >
      <div class="space-y-1 pb-4">
        <label class="form-label">Input</label>
        <input class="input-field" [ngModel]="input()" (ngModelChange)="input.set($event)" placeholder="hello world example" />
      </div>
      <div class="grid gap-2 sm:grid-cols-2">
        @for (row of rows(); track row.label) {
          <div class="flex items-center gap-2 rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2">
            <div class="min-w-0 flex-1">
              <p class="text-xs text-[var(--text-muted)]">{{ row.label }}</p>
              <p class="truncate font-mono text-sm">{{ row.value }}</p>
            </div>
            <app-copy-button [text]="row.value" />
          </div>
        }
      </div>
    </app-dev-tool-shell>
  `,
})
export class TextCaseConverterToolComponent {
  readonly input = signal('hello world example');

  readonly rows = computed(() => {
    const c = convertAllCases(this.input());
    return [
      { label: 'lowercase', value: c.lowercase },
      { label: 'UPPERCASE', value: c.uppercase },
      { label: 'Title Case', value: c.titleCase },
      { label: 'camelCase', value: c.camelCase },
      { label: 'PascalCase', value: c.pascalCase },
      { label: 'snake_case', value: c.snakeCase },
      { label: 'kebab-case', value: c.kebabCase },
      { label: 'SCREAMING_SNAKE_CASE', value: c.screamingSnakeCase },
      { label: 'dot.case', value: c.dotCase },
    ];
  });
}
