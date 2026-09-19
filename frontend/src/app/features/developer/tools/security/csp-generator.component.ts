import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

const DIRECTIVES = [
  { key: 'default-src', hint: "'self'" },
  { key: 'script-src', hint: "'self'" },
  { key: 'style-src', hint: "'self' 'unsafe-inline'" },
  { key: 'img-src', hint: "'self' data:" },
  { key: 'font-src', hint: "'self'" },
  { key: 'connect-src', hint: "'self'" },
  { key: 'frame-src', hint: "'none'" },
  { key: 'object-src', hint: "'none'" },
  { key: 'base-uri', hint: "'self'" },
  { key: 'form-action', hint: "'self'" },
];

@Component({
  selector: 'app-csp-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="csp-generator"
      title="CSP Generator"
      description="Build a Content-Security-Policy header value. Leave a directive blank to omit it."
      icon="shield"
    >
      <div class="grid gap-3 pb-4 sm:grid-cols-2">
        @for (d of directives; track d.key) {
          <div>
            <label class="form-label font-mono">{{ d.key }}</label>
            <input class="input-field font-mono text-sm" [placeholder]="d.hint" [ngModel]="values()[d.key] ?? ''" (ngModelChange)="setValue(d.key, $event)" />
          </div>
        }
      </div>
      <div class="flex items-start gap-2">
        <pre class="input-field flex-1 whitespace-pre-wrap font-mono text-sm">{{ policy() }}</pre>
        <app-copy-button [text]="policy()" />
      </div>
    </app-dev-tool-shell>
  `,
})
export class CspGeneratorToolComponent {
  readonly directives = DIRECTIVES;
  readonly values = signal<Partial<Record<string, string>>>({});

  readonly policy = computed(() =>
    this.directives
      .map((d) => this.values()[d.key]?.trim())
      .map((v, i) => (v ? `${this.directives[i].key} ${v}` : null))
      .filter((v): v is string => !!v)
      .join('; '),
  );

  setValue(key: string, value: string): void {
    this.values.set({ ...this.values(), [key]: value });
  }
}
