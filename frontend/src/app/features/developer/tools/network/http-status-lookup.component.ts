import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { HTTP_STATUS_CODES } from './http-status-codes.data';

@Component({
  selector: 'app-http-status-lookup-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="http-status-lookup"
      title="HTTP Status Code Lookup"
      description="Look up the meaning of an HTTP status code."
      icon="network"
    >
      <div class="space-y-1 pb-4">
        <label class="form-label">Search by code or name</label>
        <input class="input-field" placeholder="404" [ngModel]="query()" (ngModelChange)="query.set($event)" />
      </div>
      <ul class="space-y-2">
        @for (entry of results(); track entry.code) {
          <li class="rounded-[var(--radius-sm)] border border-[var(--border)] px-3 py-2">
            <p class="font-mono text-sm font-semibold">{{ entry.code }} {{ entry.name }}</p>
            <p class="text-xs text-[var(--text-muted)]">{{ entry.description }}</p>
          </li>
        }
        @if (results().length === 0) {
          <p class="text-sm text-[var(--text-muted)]">No status codes match "{{ query() }}".</p>
        }
      </ul>
    </app-dev-tool-shell>
  `,
})
export class HttpStatusLookupToolComponent {
  readonly query = signal('');

  readonly results = computed(() => {
    const q = this.query().trim().toLowerCase();
    if (!q) return HTTP_STATUS_CODES;
    return HTTP_STATUS_CODES.filter((e) => String(e.code).includes(q) || e.name.toLowerCase().includes(q));
  });
}
