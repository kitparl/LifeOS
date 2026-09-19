import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { parseJsonOrThrow } from './json.util';
import { evaluateJsonPath } from './jsonpath.util';

@Component({
  selector: 'app-jsonpath-tester-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="jsonpath-tester"
      title="JSONPath Tester"
      description="Test a JSONPath expression against JSON data. Supports $, ., [], [*], [n], and .. — not filter expressions."
      icon="search"
    >
      <div class="space-y-3">
        <div class="space-y-1">
          <label class="form-label">JSON data</label>
          <textarea
            class="input-field h-40 resize-y font-mono text-sm"
            placeholder='{"store": {"book": [{"title": "A"}, {"title": "B"}]}}'
            [ngModel]="jsonInput()"
            (ngModelChange)="setJsonInput($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">JSONPath expression</label>
          <input
            class="input-field font-mono text-sm"
            placeholder="$.store.book[*].title"
            [ngModel]="pathInput()"
            (ngModelChange)="setPathInput($event)"
          />
        </div>
        <div class="flex items-center justify-between">
          <label class="form-label !mb-0">Matches ({{ resultCount() }})</label>
          <app-copy-button [text]="resultText()" />
        </div>
        @if (error()) {
          <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
        } @else {
          <pre class="input-field h-48 overflow-auto whitespace-pre-wrap font-mono text-xs">{{ resultText() }}</pre>
        }
      </div>
    </app-dev-tool-shell>
  `,
})
export class JsonpathTesterToolComponent {
  readonly jsonInput = signal('');
  readonly pathInput = signal('');
  readonly error = signal<string | null>(null);
  readonly results = signal<unknown[]>([]);

  readonly resultCount = computed(() => this.results().length);
  readonly resultText = computed(() => JSON.stringify(this.results(), null, 2));

  setJsonInput(value: string): void {
    this.jsonInput.set(value);
    this.run();
  }

  setPathInput(value: string): void {
    this.pathInput.set(value);
    this.run();
  }

  private run(): void {
    if (!this.jsonInput().trim() || !this.pathInput().trim()) {
      this.results.set([]);
      this.error.set(null);
      return;
    }
    try {
      const data = parseJsonOrThrow(this.jsonInput());
      this.results.set(evaluateJsonPath(this.pathInput(), data));
      this.error.set(null);
    } catch (e) {
      this.results.set([]);
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }
}
