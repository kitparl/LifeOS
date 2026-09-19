import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

type Base = 2 | 8 | 10 | 16;
const BASES: { base: Base; label: string; prefix: string }[] = [
  { base: 2, label: 'Binary', prefix: '0b' },
  { base: 8, label: 'Octal', prefix: '0o' },
  { base: 10, label: 'Decimal', prefix: '' },
  { base: 16, label: 'Hexadecimal', prefix: '0x' },
];

@Component({
  selector: 'app-number-base-converter-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="number-base-converter"
      title="Number Base Converter"
      description="Convert a number between binary, octal, decimal, and hexadecimal."
      icon="binary"
    >
      <div class="flex flex-wrap items-end gap-3 pb-4">
        <div>
          <label class="form-label">Input base</label>
          <select class="input-field w-auto" [ngModel]="inputBase()" (ngModelChange)="setInputBase($event)">
            @for (b of bases; track b.base) {
              <option [ngValue]="b.base">{{ b.label }}</option>
            }
          </select>
        </div>
        <div class="flex-1">
          <label class="form-label">Value</label>
          <input class="input-field font-mono text-sm" [ngModel]="input()" (ngModelChange)="onInputChange($event)" />
        </div>
      </div>
      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      } @else {
        <div class="grid gap-2 sm:grid-cols-2">
          @for (b of bases; track b.base) {
            <div class="flex items-center gap-2 rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2">
              <div class="min-w-0 flex-1">
                <p class="text-xs text-[var(--text-muted)]">{{ b.label }}</p>
                <p class="truncate font-mono text-sm">{{ b.prefix }}{{ converted()[b.base] }}</p>
              </div>
              <app-copy-button [text]="b.prefix + converted()[b.base]" />
            </div>
          }
        </div>
      }
    </app-dev-tool-shell>
  `,
})
export class NumberBaseConverterToolComponent {
  readonly bases = BASES;
  readonly inputBase = signal<Base>(10);
  readonly input = signal('42');
  readonly error = signal<string | null>(null);

  readonly decimalValue = computed<number | null>(() => {
    const cleaned = this.input().trim().replace(/^0[bxo]/i, '');
    if (!cleaned) return null;
    const n = parseInt(cleaned, this.inputBase());
    return Number.isNaN(n) ? null : n;
  });

  readonly converted = computed<Record<Base, string>>(() => {
    const n = this.decimalValue();
    if (n === null) return { 2: '', 8: '', 10: '', 16: '' };
    return { 2: n.toString(2), 8: n.toString(8), 10: n.toString(10), 16: n.toString(16) };
  });

  setInputBase(base: Base): void {
    this.inputBase.set(base);
    this.validate();
  }

  onInputChange(value: string): void {
    this.input.set(value);
    this.validate();
  }

  private validate(): void {
    if (!this.input().trim()) {
      this.error.set(null);
      return;
    }
    this.error.set(this.decimalValue() === null ? `"${this.input()}" is not valid in base ${this.inputBase()}.` : null);
  }
}
