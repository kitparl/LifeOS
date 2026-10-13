import { Component, computed, input } from '@angular/core';
import { RunResult, SignatureSpec, formatJson } from '../models/dsa.models';
import { TestInputComponent } from './test-input.component';
import { VerdictBadgeComponent } from './verdict-badge.component';

/** Run output: per-case input / expected / actual, plus stdout and stderr. */
@Component({
  selector: 'app-dsa-run-results',
  standalone: true,
  imports: [TestInputComponent, VerdictBadgeComponent],
  template: `
    @let r = result();
    <div class="space-y-3" data-testid="dsa-run-results">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-sm font-medium">Run</span>
        @if (r.status === 'pending' || r.status === 'running') {
          <span class="text-xs" style="color: var(--text-muted)">{{ r.status === 'pending' ? 'Queued…' : 'Running…' }}</span>
        } @else {
          <app-dsa-verdict-badge [verdict]="r.verdict" />
          @if (checked().total > 0) {
            <span class="text-xs" style="color: var(--text-muted)" data-testid="dsa-run-summary">
              {{ checked().passed }}/{{ checked().total }} example cases passed
            </span>
          }
        }
      </div>
      @if (r.message) {
        <pre class="max-h-48 overflow-auto whitespace-pre-wrap rounded p-2 text-xs" style="background: var(--surface-2)">{{ r.message }}</pre>
      }
      @for (c of r.cases; track c.index) {
        <div class="panel--flat space-y-1 !p-3 text-xs" [attr.data-testid]="'dsa-run-case-' + c.index">
          <div class="flex flex-wrap items-center gap-2 font-medium">
            <span>Case {{ c.index + 1 }}</span>
            @if (c.passed === true) {
              <span class="badge badge--success">Passed</span>
            } @else if (c.passed === false) {
              <span class="badge badge--danger">Failed</span>
            }
            @if (c.is_custom) {
              <span class="chip !py-0 text-[0.6875rem]" title="Not one of the examples, so there's no expected output to check against">Custom</span>
            }
            @if (c.ms !== null) {
              <span style="color: var(--text-muted)">{{ c.ms.toFixed(1) }} ms</span>
            }
          </div>
          <div style="color: var(--text-muted)">Input</div>
          <app-dsa-test-input class="block pl-3" [signature]="signature()" [value]="c.input" />
          @if (!c.is_custom) {
            <div><span style="color: var(--text-muted)">Expected</span> <code class="break-all">{{ json(c.expected) }}</code></div>
          }
          @if (c.error) {
            <div class="whitespace-pre-wrap" style="color: var(--danger)">{{ c.error }}</div>
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
  readonly signature = input<SignatureSpec | null>(null);
  readonly json = formatJson;

  /** Cases that had an expected output (the examples), and how many of them passed. */
  readonly checked = computed(() => {
    const compared = this.result().cases.filter((c) => c.passed !== null);
    return { passed: compared.filter((c) => c.passed).length, total: compared.length };
  });
}
