import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { validateSqlBasic } from './sql.util';

@Component({
  selector: 'app-sql-validator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="sql-validator"
      title="SQL Validator"
      description="Check a SQL statement for basic syntax problems (balanced parentheses/quotes, recognized starting keyword) — not a full parser, and nothing runs against a database."
      icon="database"
    >
      <div class="space-y-1 pb-3">
        <label class="form-label">SQL statement</label>
        <textarea
          class="input-field h-40 resize-y font-mono text-sm"
          placeholder="SELECT * FROM users WHERE id = 1"
          [ngModel]="input()"
          (ngModelChange)="input.set($event)"
        ></textarea>
      </div>
      @if (input().trim()) {
        @if (result().valid) {
          <p class="text-sm text-[var(--success)]">No basic syntax problems found.</p>
        } @else {
          <ul class="space-y-1 text-sm text-[var(--danger)]">
            @for (issue of result().issues; track issue) {
              <li>{{ issue }}</li>
            }
          </ul>
        }
      } @else {
        <p class="text-sm text-[var(--text-muted)]">Enter a SQL statement above.</p>
      }
    </app-dev-tool-shell>
  `,
})
export class SqlValidatorToolComponent {
  readonly input = signal('');
  readonly result = computed(() => validateSqlBasic(this.input()));
}
