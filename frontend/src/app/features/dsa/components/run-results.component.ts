import { Component, input } from '@angular/core';
import { RunResult, formatJson } from '../models/dsa.models';
import { VerdictBadgeComponent } from './verdict-badge.component';

/** Run output: per-case input / expected / actual, plus stdout and stderr. */
@Component({
  selector: 'app-dsa-run-results',
  standalone: true,
  imports: [VerdictBadgeComponent],
  template: `
    @let r = result();
    <div class="space-y-3" data-testid="dsa-run-results">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-sm font-medium">Run</span>
        @if (r.status === 'pending' || r.status === 'running') {
          <span class="text-xs" style="color: var(--text-muted)">{{ r.status === 'pending' ? 'Queued…' : 'Running…' }}</span>
        } @else {
          <app-dsa-verdict-badge [verdict]="r.verdict" />
        }
      </div>
      @if (r.message) {
        <pre class="max-h-48 overflow-auto whitespace-pre-wrap rounded p-2 text-xs" style="background: var(--surface-2)">{{ r.message }}</pre>
      }
      @for (c of r.cases; track c.index) {
        <div class="panel--flat space-y-1 !p-3 text-xs" [attr.data-testid]="'dsa-run-case-' + c.index">
          <div class="flex items-center gap-2 font-medium">
            <span>{{ c.is_custom ? 'Custom ' + (c.index + 1) : 'Case ' + (c.index + 1) }}</span>
            @if (c.passed === true) {
              <span class="badge badge--success">Passed</span>
            } @else if (c.passed === false) {
              <span class="badge badge--danger">Failed</span>
            }
            @if (c.ms !== null) {
              <span style="color: var(--text-muted)">{{ c.ms.toFixed(1) }} ms</span>
            }
          </div>
          <div><span style="color: var(--text-muted)">Input</span> <code class="break-all">{{ json(c.input) }}</code></div>
          @if (!c.is_custom) {
            <div><span style="color: var(--text-muted)">Expected</span> <code class="break-all">{{ json(c.expected) }}</code></div>
          }
          @if (c.error) {
            <div style="color: var(--danger)">{{ c.error }}</div>
          } @else {
            <div><span style="color: var(--text-muted)">Output</span> <code class="break-all">{{ json(c.actual) }}</code></div>
          }
        </div>
      }
      @if (r.stdout) {
        <div class="space-y-1">
          <p class="text-xs font-medium" style="color: var(--text-muted)">stdout</p>
          <pre class="max-h-40 overflow-auto whitespace-pre-wrap rounded p-2 text-xs" style="background: var(--surface-2)">{{ r.stdout }}</pre>
        </div>
      }
      @if (r.stderr) {
        <div class="space-y-1">
          <p class="text-xs font-medium" style="color: var(--text-muted)">stderr</p>
          <pre class="max-h-40 overflow-auto whitespace-pre-wrap rounded p-2 text-xs" style="background: var(--surface-2)">{{ r.stderr }}</pre>
        </div>
      }
    </div>
  `,
})
export class RunResultsComponent {
  readonly result = input.required<RunResult>();
  readonly json = formatJson;
}
