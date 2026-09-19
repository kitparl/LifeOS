import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { explainCron } from './cron.util';

@Component({
  selector: 'app-cron-parser-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="cron-parser"
      title="Cron Expression Parser / Explainer"
      description="Explain what a 5-field cron expression means in plain English."
      icon="timer"
    >
      <div class="space-y-1 pb-3">
        <label class="form-label">Cron expression</label>
        <input
          class="input-field font-mono text-sm"
          placeholder="*/15 9-17 * * 1-5"
          [ngModel]="expression()"
          (ngModelChange)="onChange($event)"
        />
      </div>
      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      } @else if (explanation()) {
        <p class="text-base">{{ explanation() }}</p>
      } @else {
        <p class="text-sm text-[var(--text-muted)]">Enter a cron expression above.</p>
      }
    </app-dev-tool-shell>
  `,
})
export class CronParserToolComponent {
  readonly expression = signal('');
  readonly explanation = signal('');
  readonly error = signal<string | null>(null);

  onChange(value: string): void {
    this.expression.set(value);
    if (!value.trim()) {
      this.explanation.set('');
      this.error.set(null);
      return;
    }
    try {
      this.explanation.set(explainCron(value));
      this.error.set(null);
    } catch (e) {
      this.explanation.set('');
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }
}
