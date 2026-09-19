import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

@Component({
  selector: 'app-url-parser-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell toolId="url-parser" title="URL Parser" description="Break a URL down into its components." icon="link">
      <div class="space-y-1 pb-4">
        <label class="form-label">URL</label>
        <input
          class="input-field font-mono text-sm"
          placeholder="https://user:pass&#64;example.com:8080/path?a=1&b=2#section"
          [ngModel]="input()"
          (ngModelChange)="setInput($event)"
        />
      </div>
      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      }
      @if (parsed(); as u) {
        <div class="grid gap-2 sm:grid-cols-2">
          @for (row of rows(u); track row.label) {
            @if (row.value) {
              <div class="flex items-center gap-2 rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2">
                <div class="min-w-0 flex-1">
                  <p class="text-xs text-[var(--text-muted)]">{{ row.label }}</p>
                  <p class="truncate font-mono text-sm">{{ row.value }}</p>
                </div>
                <app-copy-button [text]="row.value" />
              </div>
            }
          }
        </div>
        @if (u.searchParams.size) {
          <p class="mb-1 mt-4 text-sm font-semibold">Query parameters</p>
          <ul class="space-y-1 text-sm">
            @for (entry of paramEntries(u); track entry[0] + entry[1]) {
              <li><code>{{ entry[0] }}</code> = {{ entry[1] }}</li>
            }
          </ul>
        }
      } @else if (!error()) {
        <p class="text-sm text-[var(--text-muted)]">Enter a URL above.</p>
      }
    </app-dev-tool-shell>
  `,
})
export class UrlParserToolComponent {
  readonly input = signal('');
  readonly error = signal<string | null>(null);
  readonly parsed = signal<URL | null>(null);

  readonly rows = (u: URL) => [
    { label: 'Protocol', value: u.protocol },
    { label: 'Host', value: u.host },
    { label: 'Hostname', value: u.hostname },
    { label: 'Port', value: u.port },
    { label: 'Pathname', value: u.pathname },
    { label: 'Search', value: u.search },
    { label: 'Hash', value: u.hash },
    { label: 'Origin', value: u.origin },
    { label: 'Username', value: u.username },
  ];

  paramEntries(u: URL): [string, string][] {
    return Array.from(u.searchParams.entries());
  }

  setInput(value: string): void {
    this.input.set(value);
    if (!value.trim()) {
      this.parsed.set(null);
      this.error.set(null);
      return;
    }
    try {
      this.parsed.set(new URL(value));
      this.error.set(null);
    } catch {
      this.parsed.set(null);
      this.error.set('Not a valid absolute URL (must include a scheme, e.g. https://).');
    }
  }
}
