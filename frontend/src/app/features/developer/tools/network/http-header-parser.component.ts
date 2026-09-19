import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';

interface HeaderEntry {
  name: string;
  value: string;
}

function parseHttpHeaders(raw: string): HeaderEntry[] {
  return raw
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .filter((l) => !/^HTTP\//i.test(l))
    .map((line) => {
      const idx = line.indexOf(':');
      if (idx === -1) return { name: line, value: '' };
      return { name: line.slice(0, idx).trim(), value: line.slice(idx + 1).trim() };
    });
}

@Component({
  selector: 'app-http-header-parser-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="http-header-parser"
      title="HTTP Header Parser"
      description="Parse raw HTTP headers into a readable table."
      icon="network"
    >
      <div class="space-y-1 pb-4">
        <label class="form-label">Raw headers</label>
        <textarea
          class="input-field h-40 resize-y font-mono text-sm"
          placeholder="Content-Type: application/json&#10;Cache-Control: no-cache"
          [ngModel]="input()"
          (ngModelChange)="input.set($event)"
        ></textarea>
      </div>
      @if (headers().length) {
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs text-[var(--text-muted)]">
              <th class="pb-1 pr-3">Name</th>
              <th class="pb-1">Value</th>
            </tr>
          </thead>
          <tbody>
            @for (h of headers(); track h.name + h.value) {
              <tr class="border-t border-[var(--border)]">
                <td class="py-1.5 pr-3 font-mono font-semibold">{{ h.name }}</td>
                <td class="py-1.5 font-mono">{{ h.value }}</td>
              </tr>
            }
          </tbody>
        </table>
      } @else {
        <p class="text-sm text-[var(--text-muted)]">Paste raw headers above (one "Name: Value" per line).</p>
      }
    </app-dev-tool-shell>
  `,
})
export class HttpHeaderParserToolComponent {
  readonly input = signal('');
  readonly headers = computed(() => parseHttpHeaders(this.input()));
}
