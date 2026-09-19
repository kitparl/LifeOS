import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { checkPasswordStrength } from './password-strength.util';

const SCORE_COLORS = ['var(--danger)', 'var(--danger)', 'var(--warning)', 'var(--success)', 'var(--success)'];

@Component({
  selector: 'app-password-strength-checker-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="password-strength-checker"
      title="Password Strength Checker"
      description="Check password strength entirely in your browser — never sent, logged, or saved anywhere."
      icon="shield-check"
    >
      <div class="flex items-end gap-2 pb-4">
        <div class="flex-1 space-y-1">
          <label class="form-label">Password</label>
          <input
            class="input-field font-mono text-sm"
            [type]="visible() ? 'text' : 'password'"
            autocomplete="new-password"
            [ngModel]="password()"
            (ngModelChange)="password.set($event)"
          />
        </div>
        <button type="button" class="btn-secondary" (click)="visible.set(!visible())">{{ visible() ? 'Hide' : 'Show' }}</button>
      </div>

      <div class="mb-1 h-2 overflow-hidden rounded-full bg-[var(--surface-3)]">
        <div class="h-full transition-all" [style.width.%]="(result().score + 1) * 20" [style.background]="color()"></div>
      </div>
      <p class="pb-3 text-sm font-semibold" [style.color]="color()">{{ result().label }} — ~{{ result().entropyBits }} bits of entropy</p>

      @if (result().feedback.length) {
        <ul class="list-disc space-y-1 pl-5 text-sm text-[var(--text-muted)]">
          @for (f of result().feedback; track f) {
            <li>{{ f }}</li>
          }
        </ul>
      }
    </app-dev-tool-shell>
  `,
})
export class PasswordStrengthCheckerToolComponent {
  readonly password = signal('');
  readonly visible = signal(false);

  readonly result = computed(() => checkPasswordStrength(this.password()));
  readonly color = computed(() => SCORE_COLORS[this.result().score]);
}
