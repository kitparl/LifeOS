import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { calculateCidr } from './cidr.util';

@Component({
  selector: 'app-cidr-calculator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="cidr-calculator"
      title="CIDR Calculator"
      description="Calculate network range, mask, and host count from an IPv4 CIDR block."
      icon="router"
    >
      <div class="space-y-1 pb-4">
        <label class="form-label">CIDR</label>
        <input class="input-field font-mono text-sm" placeholder="192.168.1.0/24" [ngModel]="input()" (ngModelChange)="setInput($event)" />
      </div>
      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      }
      @if (info(); as i) {
        <div class="grid gap-2 sm:grid-cols-2">
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Network address</p><p class="font-mono text-sm">{{ i.network }}</p></div>
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Broadcast address</p><p class="font-mono text-sm">{{ i.broadcast }}</p></div>
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Netmask</p><p class="font-mono text-sm">{{ i.netmask }} (/{{ i.prefixLength }})</p></div>
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Wildcard mask</p><p class="font-mono text-sm">{{ i.wildcard }}</p></div>
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">First usable host</p><p class="font-mono text-sm">{{ i.firstHost }}</p></div>
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Last usable host</p><p class="font-mono text-sm">{{ i.lastHost }}</p></div>
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Total addresses</p><p class="font-mono text-sm">{{ i.totalAddresses }}</p></div>
          <div class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2"><p class="text-xs text-[var(--text-muted)]">Usable hosts</p><p class="font-mono text-sm">{{ i.usableHosts }}</p></div>
        </div>
      } @else if (!error()) {
        <p class="text-sm text-[var(--text-muted)]">Enter a CIDR block above, e.g. 10.0.0.0/16.</p>
      }
    </app-dev-tool-shell>
  `,
})
export class CidrCalculatorToolComponent {
  readonly input = signal('');
  readonly error = signal<string | null>(null);
  readonly info = signal<ReturnType<typeof calculateCidr> | null>(null);

  setInput(value: string): void {
    this.input.set(value);
    if (!value.trim()) {
      this.info.set(null);
      this.error.set(null);
      return;
    }
    try {
      this.info.set(calculateCidr(value));
      this.error.set(null);
    } catch (e) {
      this.info.set(null);
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }
}
