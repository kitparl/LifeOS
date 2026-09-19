import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

type SriAlgo = 'SHA-256' | 'SHA-384' | 'SHA-512';
const ALGOS: SriAlgo[] = ['SHA-256', 'SHA-384', 'SHA-512'];
const PREFIX: Record<SriAlgo, string> = { 'SHA-256': 'sha256', 'SHA-384': 'sha384', 'SHA-512': 'sha512' };

function bufferToBase64(buf: ArrayBuffer): string {
  let binary = '';
  for (const byte of new Uint8Array(buf)) binary += String.fromCharCode(byte);
  return btoa(binary);
}

@Component({
  selector: 'app-sri-hash-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="sri-hash-generator"
      title="SRI Hash Generator"
      description="Generate a Subresource Integrity hash for a local file or pasted content. Files are read locally and never uploaded."
      icon="shield-check"
    >
      <div class="flex flex-wrap items-end gap-3 pb-4">
        <div>
          <label class="form-label">Algorithm</label>
          <select class="input-field w-auto" [ngModel]="algo()" (ngModelChange)="setAlgo($event)">
            @for (a of algos; track a) {
              <option [ngValue]="a">{{ a }}</option>
            }
          </select>
        </div>
        <div>
          <label class="form-label">Local file</label>
          <input class="input-field" type="file" (change)="onFileChange($event)" />
        </div>
      </div>

      <div class="space-y-1 pb-4">
        <label class="form-label">Or paste content</label>
        <textarea
          class="input-field h-32 resize-y font-mono text-sm"
          placeholder="console.log('hello');"
          [ngModel]="pastedText()"
          (ngModelChange)="onPastedTextChange($event)"
        ></textarea>
      </div>

      @if (integrity()) {
        <div class="flex items-center gap-2 pb-2">
          <input class="input-field font-mono text-sm" readonly [ngModel]="integrity()" />
          <app-copy-button [text]="integrity()" />
        </div>
        <pre class="input-field overflow-auto whitespace-pre-wrap font-mono text-xs">{{ snippet() }}</pre>
      } @else {
        <p class="text-sm text-[var(--text-muted)]">Choose a file or paste content above.</p>
      }
    </app-dev-tool-shell>
  `,
})
export class SriHashGeneratorToolComponent {
  readonly algos = ALGOS;
  readonly algo = signal<SriAlgo>('SHA-384');
  readonly pastedText = signal('');
  readonly integrity = signal('');

  setAlgo(value: SriAlgo): void {
    this.algo.set(value);
    if (this.pastedText()) this.computeFromText(this.pastedText());
  }

  onPastedTextChange(value: string): void {
    this.pastedText.set(value);
    if (value) this.computeFromText(value);
    else this.integrity.set('');
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const buf = reader.result as ArrayBuffer;
      void this.computeFromBuffer(buf);
    };
    reader.readAsArrayBuffer(file);
  }

  private computeFromText(text: string): void {
    void this.computeFromBuffer(new TextEncoder().encode(text).buffer as ArrayBuffer);
  }

  private async computeFromBuffer(buf: ArrayBuffer): Promise<void> {
    const digest = await crypto.subtle.digest(this.algo(), buf);
    this.integrity.set(`${PREFIX[this.algo()]}-${bufferToBase64(digest)}`);
  }

  snippet(): string {
    return `<script src="https://example.com/script.js"\n        integrity="${this.integrity()}"\n        crossorigin="anonymous"></script>`;
  }
}
