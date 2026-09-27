import { Component, input } from '@angular/core';
import { LANGUAGE_LABELS, SubmissionDetail } from '../models/dsa.models';
import { VerdictBadgeComponent } from './verdict-badge.component';

/** Submit outcome. Hidden tests are never shown: only which case failed. */
@Component({
  selector: 'app-dsa-submission-result',
  standalone: true,
  imports: [VerdictBadgeComponent],
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
          @if (s.failed_case !== null) {
            <div>
              <dt style="color: var(--text-muted)">Failed on</dt>
              <dd class="font-medium">Test {{ s.failed_case }}</dd>
            </div>
          }
        </dl>
        @if (s.message) {
          <pre class="max-h-48 overflow-auto whitespace-pre-wrap rounded p-2 text-xs" style="background: var(--surface-2)">{{ s.message }}</pre>
        }
      }
    </div>
  `,
})
export class SubmissionResultComponent {
  readonly submission = input.required<SubmissionDetail>();
  readonly languages = LANGUAGE_LABELS;
}
