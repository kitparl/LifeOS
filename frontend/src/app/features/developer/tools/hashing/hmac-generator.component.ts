import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { HmacAlgo, computeHmac } from './hash.util';

const ALGOS: HmacAlgo[] = ['SHA-1', 'SHA-256', 'SHA-512'];

@Component({
  selector: 'app-hmac-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="hmac-generator"
      title="HMAC Generator"
      description="Generate an HMAC using a secret key, computed locally with the Web Crypto API."
      icon="key-round"
    >
      <div class="flex flex-wrap items-end justify-between gap-3 pb-3">
        <div class="flex items-center gap-2">
          <label class="form-label !mb-0">Algorithm</label>
          <select class="input-field w-auto" [ngModel]="algo()" (ngModelChange)="setAlgo($event)">
            @for (a of algos; track a) {
              <option [ngValue]="a">HMAC-{{ a }}</option>
            }
          </select>
        </div>
        <app-copy-button [text]="output()" />
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">Secret key</label>
          <input
            class="input-field font-mono text-sm"
            placeholder="Secret key…"
            [ngModel]="key()"
            (ngModelChange)="onKeyChange($event)"
          />
        </div>
        <div class="space-y-1">
          <label class="form-label">Message</label>
          <input
            class="input-field font-mono text-sm"
            placeholder="Message…"
            [ngModel]="message()"
            (ngModelChange)="onMessageChange($event)"
          />
        </div>
      </div>
      <div class="mt-3 space-y-1">
        <label class="form-label">HMAC-{{ algo() }}</label>
        <input class="input-field font-mono text-sm" readonly [ngModel]="output()" />
      </div>
    </app-dev-tool-shell>
  `,
})
export class HmacGeneratorToolComponent {
  readonly algos = ALGOS;
  readonly algo = signal<HmacAlgo>('SHA-256');
  readonly key = signal('');
  readonly message = signal('');
  readonly output = signal('');

  setAlgo(value: HmacAlgo): void {
    this.algo.set(value);
    this.run();
  }

  onKeyChange(value: string): void {
    this.key.set(value);
    this.run();
  }

  onMessageChange(value: string): void {
    this.message.set(value);
    this.run();
  }

  private run(): void {
    if (!this.key() || !this.message()) {
      this.output.set('');
      return;
    }
    computeHmac(this.algo(), this.key(), this.message()).then((hmac) => this.output.set(hmac));
  }
}
