import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { generateRandomString } from './generators.util';

@Component({
  selector: 'app-api-key-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="api-key-generator"
      title="API-Key-like Random String Generator"
      description="Generate an API-key-shaped random string, e.g. for local test fixtures."
      icon="key-round"
    >
      <div class="flex flex-wrap items-end justify-between gap-4 pb-3">
        <div class="flex flex-wrap items-end gap-4">
          <div>
            <label class="form-label">Prefix</label>
            <input class="input-field w-32" [ngModel]="prefix()" (ngModelChange)="setPrefix($event)" placeholder="sk_live_" />
          </div>
          <div>
            <label class="form-label">Length</label>
            <input class="input-field w-24" type="number" min="8" max="128" [ngModel]="length()" (ngModelChange)="setLength(+$event)" />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="btn-primary" (click)="regenerate()">Generate</button>
          <app-copy-button [text]="output()" />
        </div>
      </div>
      <input class="input-field font-mono text-sm" readonly [ngModel]="output()" />
    </app-dev-tool-shell>
  `,
})
export class ApiKeyGeneratorToolComponent implements OnInit {
  readonly prefix = signal('sk_live_');
  readonly length = signal(32);
  readonly output = signal('');

  ngOnInit(): void {
    this.regenerate();
  }

  setPrefix(v: string): void {
    this.prefix.set(v);
  }

  setLength(v: number): void {
    this.length.set(Math.min(128, Math.max(8, v || 8)));
  }

  regenerate(): void {
    const body = generateRandomString({ length: this.length(), lowercase: true, uppercase: true, numbers: true, symbols: false });
    this.output.set(this.prefix() + body);
  }
}
