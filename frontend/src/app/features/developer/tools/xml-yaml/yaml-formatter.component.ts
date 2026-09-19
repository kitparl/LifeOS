import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { parseYaml, stringifyYaml } from '../../shared/yaml.util';

@Component({
  selector: 'app-yaml-formatter-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="yaml-formatter"
      title="YAML Formatter"
      description="Pretty-print and validate YAML (common block/flow subset — no anchors or multi-doc)."
      icon="file-code"
    >
      <div class="flex justify-end gap-2 pb-3">
        <button type="button" class="btn-ghost" (click)="clear()">Clear</button>
        <app-copy-button [text]="output()" />
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">YAML input</label>
          <textarea
            class="input-field h-64 resize-y font-mono text-sm"
            placeholder="name: Ada&#10;active: true"
            [ngModel]="input()"
            (ngModelChange)="onInputChange($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">
            Output
            @if (valid() === true) {
              <span class="badge" style="background: var(--success-soft); color: var(--success);">Valid</span>
            } @else if (valid() === false) {
              <span class="badge" style="background: var(--danger-soft); color: var(--danger);">Invalid</span>
            }
          </label>
          <textarea class="input-field h-64 resize-y font-mono text-sm" readonly [ngModel]="output()"></textarea>
          @if (error()) {
            <p class="text-xs text-[var(--danger)]">{{ error() }}</p>
          }
        </div>
      </div>
    </app-dev-tool-shell>
  `,
})
export class YamlFormatterToolComponent implements OnInit {
  readonly input = signal('');
  readonly output = signal('');
  readonly error = signal<string | null>(null);
  readonly valid = signal<boolean | null>(null);

  ngOnInit(): void {
    this.run();
  }

  onInputChange(value: string): void {
    this.input.set(value);
    this.run();
  }

  clear(): void {
    this.input.set('');
    this.run();
  }

  private run(): void {
    const text = this.input();
    if (!text.trim()) {
      this.output.set('');
      this.error.set(null);
      this.valid.set(null);
      return;
    }
    try {
      this.output.set(stringifyYaml(parseYaml(text)));
      this.valid.set(true);
      this.error.set(null);
    } catch (e) {
      this.valid.set(false);
      this.output.set('');
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }
}
