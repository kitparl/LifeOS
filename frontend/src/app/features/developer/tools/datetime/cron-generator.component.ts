import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { buildCronExpression, explainCron } from './cron.util';

@Component({
  selector: 'app-cron-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="cron-generator"
      title="Cron Expression Generator"
      description="Build a cron expression from a schedule. Use * for 'every'."
      icon="timer"
    >
      <div class="grid grid-cols-2 gap-3 pb-3 sm:grid-cols-5">
        <div>
          <label class="form-label">Minute</label>
          <input class="input-field font-mono" [ngModel]="minute()" (ngModelChange)="minute.set($event)" />
        </div>
        <div>
          <label class="form-label">Hour</label>
          <input class="input-field font-mono" [ngModel]="hour()" (ngModelChange)="hour.set($event)" />
        </div>
        <div>
          <label class="form-label">Day of month</label>
          <input class="input-field font-mono" [ngModel]="dayOfMonth()" (ngModelChange)="dayOfMonth.set($event)" />
        </div>
        <div>
          <label class="form-label">Month</label>
          <input class="input-field font-mono" [ngModel]="month()" (ngModelChange)="month.set($event)" />
        </div>
        <div>
          <label class="form-label">Day of week</label>
          <input class="input-field font-mono" [ngModel]="dayOfWeek()" (ngModelChange)="dayOfWeek.set($event)" />
        </div>
      </div>
      <div class="flex items-center gap-2 pb-2">
        <input class="input-field font-mono text-sm" readonly [ngModel]="expression()" />
        <app-copy-button [text]="expression()" />
      </div>
      <p class="text-sm text-[var(--text-muted)]">{{ explanation() }}</p>
    </app-dev-tool-shell>
  `,
})
export class CronGeneratorToolComponent {
  readonly minute = signal('0');
  readonly hour = signal('9');
  readonly dayOfMonth = signal('*');
  readonly month = signal('*');
  readonly dayOfWeek = signal('*');

  readonly expression = computed(() =>
    buildCronExpression({
      minute: this.minute() || '*',
      hour: this.hour() || '*',
      dayOfMonth: this.dayOfMonth() || '*',
      month: this.month() || '*',
      dayOfWeek: this.dayOfWeek() || '*',
    }),
  );

  readonly explanation = computed(() => {
    try {
      return explainCron(this.expression());
    } catch (e) {
      return e instanceof Error ? e.message : String(e);
    }
  });
}
