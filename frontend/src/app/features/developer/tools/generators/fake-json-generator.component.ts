import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { parseJsonOrThrow } from '../json/json.util';
import { FAKE_JSON_PLACEHOLDERS, generateFakeData } from './generators.util';

const DEFAULT_TEMPLATE = `{
  "id": "{{uuid}}",
  "name": "{{name}}",
  "email": "{{email}}",
  "city": "{{city}}",
  "active": "{{boolean}}"
}`;

@Component({
  selector: 'app-fake-json-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="fake-json-generator"
      title="Fake JSON Data Generator"
      description="Generate fake JSON data from a template. Placeholders: {{ placeholders }}"
      icon="braces"
    >
      <div class="flex flex-wrap items-end justify-between gap-3 pb-3">
        <div>
          <label class="form-label">Count</label>
          <input class="input-field w-24" type="number" min="1" max="200" [ngModel]="count()" (ngModelChange)="setCount(+$event)" />
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="btn-primary" (click)="run()">Generate</button>
          <app-copy-button [text]="output()" />
        </div>
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">Template (use placeholders as string values)</label>
          <textarea
            class="input-field h-64 resize-y font-mono text-sm"
            [ngModel]="template()"
            (ngModelChange)="setTemplate($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">Output</label>
          <textarea class="input-field h-64 resize-y font-mono text-sm" readonly [ngModel]="output()"></textarea>
          @if (error()) {
            <p class="text-xs text-[var(--danger)]">{{ error() }}</p>
          }
        </div>
      </div>
    </app-dev-tool-shell>
  `,
})
export class FakeJsonGeneratorToolComponent implements OnInit {
  readonly placeholders = FAKE_JSON_PLACEHOLDERS.map((p) => `{{${p}}}`).join(', ');
  readonly template = signal(DEFAULT_TEMPLATE);
  readonly count = signal(3);
  readonly output = signal('');
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.run();
  }

  setTemplate(value: string): void {
    this.template.set(value);
  }

  setCount(value: number): void {
    this.count.set(Math.min(200, Math.max(1, value || 1)));
  }

  run(): void {
    try {
      const parsed = parseJsonOrThrow(this.template());
      this.output.set(JSON.stringify(generateFakeData(parsed, this.count()), null, 2));
      this.error.set(null);
    } catch (e) {
      this.output.set('');
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }
}
