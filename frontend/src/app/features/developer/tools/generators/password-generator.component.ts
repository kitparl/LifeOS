import { Component, OnInit, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { generateRandomString, passwordStrengthBits, RandomStringOptions } from './generators.util';

@Component({
  selector: 'app-password-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="password-generator"
      title="Password Generator"
      description="Generate a strong random password using secure browser randomness. Never stored or logged."
      icon="lock"
    >
      <div class="flex flex-wrap items-end justify-between gap-4 pb-3">
        <div class="flex flex-wrap items-end gap-4">
          <div>
            <label class="form-label">Length</label>
            <input class="input-field w-24" type="number" min="4" max="128" [ngModel]="length()" (ngModelChange)="setLength(+$event)" />
          </div>
          <label class="flex items-center gap-1.5 pb-1.5 text-sm"><input type="checkbox" [ngModel]="lowercase()" (ngModelChange)="set('lowercase', $event)" /> a-z</label>
          <label class="flex items-center gap-1.5 pb-1.5 text-sm"><input type="checkbox" [ngModel]="uppercase()" (ngModelChange)="set('uppercase', $event)" /> A-Z</label>
          <label class="flex items-center gap-1.5 pb-1.5 text-sm"><input type="checkbox" [ngModel]="numbers()" (ngModelChange)="set('numbers', $event)" /> 0-9</label>
          <label class="flex items-center gap-1.5 pb-1.5 text-sm"><input type="checkbox" [ngModel]="symbols()" (ngModelChange)="set('symbols', $event)" /> !&#64;#</label>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="btn-primary" (click)="regenerate()">Generate</button>
          <app-copy-button [text]="output()" />
        </div>
      </div>
      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      }
      <input class="input-field font-mono text-lg" readonly [ngModel]="output()" />
      <p class="mt-1 text-xs text-[var(--text-muted)]">~{{ strengthBits() }} bits of entropy</p>
    </app-dev-tool-shell>
  `,
})
export class PasswordGeneratorToolComponent implements OnInit {
  readonly length = signal(20);
  readonly lowercase = signal(true);
  readonly uppercase = signal(true);
  readonly numbers = signal(true);
  readonly symbols = signal(true);
  readonly output = signal('');
  readonly error = signal<string | null>(null);

  readonly strengthBits = computed(() =>
    passwordStrengthBits({
      length: this.length(),
      lowercase: this.lowercase(),
      uppercase: this.uppercase(),
      numbers: this.numbers(),
      symbols: this.symbols(),
    }),
  );

  ngOnInit(): void {
    this.regenerate();
  }

  setLength(v: number): void {
    this.length.set(Math.min(128, Math.max(4, v || 4)));
  }

  set(key: 'lowercase' | 'uppercase' | 'numbers' | 'symbols', value: boolean): void {
    ({ lowercase: this.lowercase, uppercase: this.uppercase, numbers: this.numbers, symbols: this.symbols })[key].set(value);
  }

  regenerate(): void {
    const opts: RandomStringOptions = {
      length: this.length(),
      lowercase: this.lowercase(),
      uppercase: this.uppercase(),
      numbers: this.numbers(),
      symbols: this.symbols(),
    };
    try {
      this.output.set(generateRandomString(opts));
      this.error.set(null);
    } catch (e) {
      this.output.set('');
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }
}
