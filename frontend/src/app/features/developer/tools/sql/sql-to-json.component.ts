import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { sqlInsertToJson } from './sql.util';

@Component({
  selector: 'app-sql-to-json-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="sql-to-json"
      title="SQL → JSON"
      description="Convert a SQL INSERT statement into a JSON array of objects."
      icon="database"
    >
      <div class="flex justify-end pb-3">
        <app-copy-button [text]="output()" />
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">SQL</label>
          <textarea
            class="input-field h-56 resize-y font-mono text-sm"
            placeholder="INSERT INTO users (id, name) VALUES (1, 'Ada'), (2, 'Alan');"
            [ngModel]="input()"
            (ngModelChange)="onChange($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">JSON</label>
          <textarea class="input-field h-56 resize-y font-mono text-sm" readonly [ngModel]="output()"></textarea>
          @if (error()) {
            <p class="text-xs text-[var(--danger)]">{{ error() }}</p>
          }
        </div>
      </div>
    </app-dev-tool-shell>
  `,
})
export class SqlToJsonToolComponent {
  readonly input = signal('');
  readonly output = signal('');
  readonly error = signal<string | null>(null);

  onChange(value: string): void {
    this.input.set(value);
    if (!value.trim()) {
      this.output.set('');
      this.error.set(null);
      return;
    }
    try {
      this.output.set(JSON.stringify(sqlInsertToJson(value), null, 2));
      this.error.set(null);
    } catch (e) {
      this.output.set('');
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }
}
