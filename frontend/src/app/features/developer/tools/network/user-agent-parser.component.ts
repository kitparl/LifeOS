import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { parseUserAgent } from './user-agent.util';

@Component({
  selector: 'app-user-agent-parser-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="user-agent-parser"
      title="User-Agent Parser"
      description="Parse a User-Agent string into browser, OS, and device type using local pattern matching — no external lookup service."
      icon="network"
    >
      <div class="flex items-end gap-3 pb-4">
        <div class="flex-1 space-y-1">
          <label class="form-label">User-Agent string</label>
          <input class="input-field font-mono text-sm" [ngModel]="input()" (ngModelChange)="input.set($event)" />
        </div>
        <button type="button" class="btn-secondary" (click)="useMine()">Use my browser</button>
      </div>
      @if (result(); as r) {
        <div class="grid gap-2 sm:grid-cols-2">
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Browser</p><p class="font-mono text-sm">{{ r.browser }} {{ r.browserVersion }}</p></div>
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Operating system</p><p class="font-mono text-sm">{{ r.os }}</p></div>
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Device type</p><p class="font-mono text-sm">{{ r.deviceType }}</p></div>
        </div>
      } @else {
        <p class="text-sm text-[var(--text-muted)]">Paste a User-Agent string above.</p>
      }
    </app-dev-tool-shell>
  `,
})
export class UserAgentParserToolComponent {
  readonly input = signal('');
  readonly result = computed(() => (this.input().trim() ? parseUserAgent(this.input()) : null));

  useMine(): void {
    this.input.set(navigator.userAgent);
  }
}
