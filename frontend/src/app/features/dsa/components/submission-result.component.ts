import { Component, input, output } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { JsonValue, LANGUAGE_LABELS, SignatureSpec, SubmissionDetail, formatJson } from '../models/dsa.models';
import { TestInputComponent } from './test-input.component';
import { VerdictBadgeComponent } from './verdict-badge.component';

/** Submit outcome, with the first failing test (input, expected and your output) when there is one. */
@Component({
  selector: 'app-dsa-submission-result',
  standalone: true,
  imports: [LucideDynamicIcon, TestInputComponent, VerdictBadgeComponent],
  template: `
    @let s = submission();
    <div class="space-y-2" data-testid="dsa-submission-result">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-sm font-medium">Submission</span>
        @if (s.status === 'pending' || s.status === 'running') {
          <span class="text-xs" style="color: var(--text-muted)">{{ s.status === 'pending' ? 'Queued…' : 'Judging…' }}</span>
        } @else {
          <app-dsa-verdict-badge [verdict]="s.verdict" />
          <span class="text-xs" style="color: var(--text-muted)">{{ languages[s.language] }}</span>
        }
      </div>
      @if (s.status === 'done' || s.status === 'error') {
        <dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-4">
          <div>
            <dt style="color: var(--text-muted)">Tests passed</dt>
            <dd class="font-medium">{{ s.passed }}/{{ s.total }}</dd>
          </div>
          @if (s.runtime_ms !== null) {
            <div>
              <dt style="color: var(--text-muted)">Runtime</dt>
              <dd class="font-medium">{{ s.runtime_ms }} ms</dd>
            </div>
          }
          @if (s.memory_kb !== null) {
            <div>
              <dt style="color: var(--text-muted)">Memory</dt>
              <dd class="font-medium">{{ (s.memory_kb / 1024).toFixed(1) }} MB</dd>
            </div>
          }
          @if (s.failed_case !== null && !s.failed_test) {
            <div>
              <dt style="color: var(--text-muted)">Failed on</dt>
              <dd class="font-medium">Test {{ s.failed_case }}</dd>
            </div>
          }
        </dl>
        @if (s.message && s.message !== s.failed_test?.error) {
          <pre class="max-h-48 overflow-auto whitespace-pre-wrap rounded p-2 text-xs" style="background: var(--surface-2)">{{ s.message }}</pre>
        }
        @if (s.failed_test; as t) {
          <div class="panel--flat space-y-1 !p-3 text-xs" data-testid="dsa-submission-failed-test">
            <div class="flex flex-wrap items-center gap-2 font-medium">
              <span>Failed on test {{ s.failed_case }}</span>
              <span class="chip !py-0 text-[0.6875rem]">{{ t.is_sample ? 'Example' : 'Hidden' }}</span>
              @if (canUseAsTestCase()) {
                <button type="button" class="btn-ghost !min-h-7 !px-2 text-xs ml-auto" data-testid="dsa-submission-use-case-button"
                  title="Add this input to your Run test cases" (click)="useAsTestCase.emit(t.input)">
                  <svg class="h-3.5 w-3.5" lucideIcon="plus" aria-hidden="true"></svg>
                  Use as test case
                </button>
              }
            </div>
            <div style="color: var(--text-muted)">Input</div>
            <app-dsa-test-input class="block pl-3" [signature]="signature()" [value]="t.input" />
            <div><span style="color: var(--text-muted)">Expected</span> <code class="break-all">{{ json(t.expected) }}</code></div>
            @if (t.error) {
              <div class="whitespace-pre-wrap" style="color: var(--danger)">{{ t.error }}</div>
            } @else if (t.answered) {
              <div><span style="color: var(--text-muted)">Output</span> <code class="break-all">{{ json(t.actual) }}</code></div>
            } @else {
              <div style="color: var(--text-muted)">No output: your program was stopped on this test.</div>
            }
          </div>
        }
      }
    </div>
  `,
})
export class SubmissionResultComponent {
  readonly submission = input.required<SubmissionDetail>();
  readonly signature = input<SignatureSpec | null>(null);
  /** Whether to offer "Use as test case" (needs a parent that owns Run test cases). */
  readonly canUseAsTestCase = input(false);
  readonly useAsTestCase = output<JsonValue>();

  readonly languages = LANGUAGE_LABELS;
  readonly json = formatJson;
}
