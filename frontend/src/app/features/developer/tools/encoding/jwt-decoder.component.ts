import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { decodeJwt, DecodedJwt } from './jwt.util';

@Component({
  selector: 'app-jwt-decoder-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="jwt-decoder"
      title="JWT Decode / Inspector"
      description="Decode a JSON Web Token and inspect its header, payload, and expiry. The signature is never verified — no secret is used, and nothing is sent to a server."
      icon="key-round"
    >
      <div class="flex justify-end gap-2 pb-3">
        <button type="button" class="btn-ghost" (click)="clear()">Clear</button>
      </div>
      <div class="space-y-1 pb-4">
        <label class="form-label">Token</label>
        <textarea
          class="input-field h-28 resize-y font-mono text-sm"
          placeholder="Paste a JWT (header.payload.signature)…"
          [ngModel]="token()"
          (ngModelChange)="onTokenChange($event)"
        ></textarea>
      </div>

      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      } @else if (decoded()) {
        <div class="grid gap-4 md:grid-cols-2">
          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <label class="form-label">Header</label>
              <app-copy-button [text]="headerJson()" label="Copy" />
            </div>
            <pre class="input-field h-40 overflow-auto whitespace-pre-wrap font-mono text-xs">{{ headerJson() }}</pre>
          </div>
          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <label class="form-label">Payload</label>
              <app-copy-button [text]="payloadJson()" label="Copy" />
            </div>
            <pre class="input-field h-40 overflow-auto whitespace-pre-wrap font-mono text-xs">{{ payloadJson() }}</pre>
          </div>
        </div>
        <div class="mt-3 flex flex-wrap gap-4 text-sm">
          @if (decoded()!.issuedAt) {
            <p><span class="text-[var(--text-muted)]">Issued at:</span> {{ decoded()!.issuedAt }}</p>
          }
          @if (decoded()!.expiresAt) {
            <p>
              <span class="text-[var(--text-muted)]">Expires:</span> {{ decoded()!.expiresAt }}
              @if (decoded()!.isExpired) {
                <span class="badge" style="background: var(--danger-soft); color: var(--danger);">Expired</span>
              } @else {
                <span class="badge" style="background: var(--success-soft); color: var(--success);">Valid</span>
              }
            </p>
          }
        </div>
      } @else {
        <p class="text-sm text-[var(--text-muted)]">Paste a token above to decode it.</p>
      }
    </app-dev-tool-shell>
  `,
})
export class JwtDecoderToolComponent {
  readonly token = signal('');
  readonly decoded = signal<DecodedJwt | null>(null);
  readonly error = signal<string | null>(null);

  onTokenChange(value: string): void {
    this.token.set(value);
    if (!value.trim()) {
      this.decoded.set(null);
      this.error.set(null);
      return;
    }
    try {
      this.decoded.set(decodeJwt(value));
      this.error.set(null);
    } catch (e) {
      this.decoded.set(null);
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }

  clear(): void {
    this.onTokenChange('');
  }

  headerJson(): string {
    return JSON.stringify(this.decoded()?.header, null, 2);
  }

  payloadJson(): string {
    return JSON.stringify(this.decoded()?.payload, null, 2);
  }
}
