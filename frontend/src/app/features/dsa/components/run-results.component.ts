import { Component, computed, input, signal } from '@angular/core';
import { RunResult, SignatureSpec, formatJson } from '../models/dsa.models';
import { TestInputComponent } from './test-input.component';
import { VerdictBadgeComponent } from './verdict-badge.component';

/** Run output: one tab per case (like the Test cases panel) showing input / expected / actual, plus stdout and stderr. */
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
          <app-dsa-verdict-badge [verdict]="verdict()" />
          @if (checked().total > 0) {
            <span class="text-xs" style="color: var(--text-muted)" data-testid="dsa-run-summary">
              {{ checked().passed }}/{{ checked().total }} cases passed
            </span>
          }
        }
      </div>
      @if (stoppedOn(); as n) {
        <p class="text-xs" style="color: var(--danger)" data-testid="dsa-run-stopped-case">
          Your program was stopped on case {{ n }}, so it has no output and later cases didn't run.
        </p>
      }
      @if (r.message) {
        <pre class="max-h-48 overflow-auto whitespace-pre-wrap rounded p-2 text-xs" style="background: var(--surface-2)">{{ r.message }}</pre>
      }
      @if (r.cases.length > 0) {
        <div class="flex flex-wrap items-center gap-1.5" aria-label="Run cases">
          @for (c of r.cases; track c.index) {
            <button type="button" class="chip" [attr.aria-pressed]="c.index === current()" [attr.data-testid]="'dsa-run-tab-' + c.index"
              [style.border-color]="c.index === current() ? 'var(--primary)' : null"
              [style.color]="c.index === current() ? 'var(--primary-hover)' : null"
              (click)="pick(c.index)">
              Case {{ c.index + 1 }}
              @if (c.passed === true) {
                <span style="color: var(--success)" title="Passed">•</span>
              } @else if (c.passed === false || c.error) {
                <span style="color: var(--danger)" title="Failed">•</span>
              }
            </button>
          }
        </div>
      }
      @if (selectedCase(); as c) {
        <div class="panel--flat space-y-1 !p-3 text-xs" [attr.data-testid]="'dsa-run-case-' + c.index">
          <div class="flex flex-wrap items-center gap-2 font-medium">
            <span>Case {{ c.index + 1 }}</span>
            @if (c.passed === true) {
              <span class="badge badge--success">Passed</span>
            } @else if (c.passed === false) {
              <span class="badge badge--danger">Failed</span>
            }
            @if (c.is_custom) {
              <span class="chip !py-0 text-[0.6875rem]" [attr.title]="c.passed !== null ? 'Expected output from our reference solution' : null">Custom</span>
            }
            @if (c.ms !== null) {
              <span style="color: var(--text-muted)">{{ c.ms.toFixed(1) }} ms</span>
            }
          </div>
          <div style="color: var(--text-muted)">Input</div>
          <app-dsa-test-input class="block pl-3" [signature]="signature()" [value]="c.input" />
          @if (c.passed !== null) {
            <div><span style="color: var(--text-muted)">Expected</span> <code class="break-all">{{ json(c.expected) }}</code></div>
          }
          @if (c.unchecked_reason) {
            <div style="color: var(--text-muted)" [attr.data-testid]="'dsa-run-case-unchecked-' + c.index">{{ c.unchecked_reason }}</div>
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

  /** Cases that were compared (examples, and custom cases checked by the reference), and how many passed. */
  readonly checked = computed(() => {
    const compared = this.result().cases.filter((c) => c.passed !== null);
    return { passed: compared.filter((c) => c.passed).length, total: compared.length };
  });

  /** "Accepted" would claim correctness when only custom cases ran and nothing was compared. */
  readonly verdict = computed(() => {
    const verdict = this.result().verdict;
    return verdict === 'Accepted' && this.checked().total === 0 ? 'Finished' : verdict;
  });

  /** The case tab the user picked, tied to the result it was picked on (a new Run starts fresh). */
  private readonly picked = signal<{ run: RunResult; index: number } | null>(null);

  /** Index of the case shown: the user's pick, else the first failed case, else the first case. */
  readonly current = computed(() => {
    const run = this.result();
    const picked = this.picked();
    if (picked?.run === run) return picked.index;
    const failed = run.cases.find((c) => c.passed === false || c.error);
    return (failed ?? run.cases[0])?.index ?? null;
  });

  readonly selectedCase = computed(() => this.result().cases.find((c) => c.index === this.current()) ?? null);

  pick(index: number): void {
    this.picked.set({ run: this.result(), index });
  }

  /** The 1-based case the program died on without writing a result (TLE, MLE, crash), if any. */
  readonly stoppedOn = computed(() => {
    const { failed_case, cases } = this.result();
    return failed_case !== null && !cases.some((c) => c.index === failed_case - 1) ? failed_case : null;
  });
}
