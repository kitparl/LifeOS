import { Component, Input, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  DIMENSION_LABELS,
  WritingEvaluation,
} from './models/communication.models';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-writing-feedback-panel',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="panel text-sm space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <p class="font-medium" style="color: var(--text)">AI Feedback</p>
        <button
          type="button"
          class="btn-primary text-xs"
          [disabled]="busy() || !writingId"
          (click)="runFeedback()"
        >
          {{ busy() ? 'Evaluating…' : 'AI Feedback' }}
        </button>
      </div>

      @if (errorCode() === 'missing_credential' || errorCode() === 'invalid_credential') {
        <div class="text-xs space-y-1" style="color: var(--danger)">
          <p>{{ errorMessage() }}</p>
          <a routerLink="/integrations" class="link">Open Integrations → Sarvam</a>
        </div>
      } @else if (errorMessage()) {
        <p class="text-xs" style="color: var(--danger)">{{ errorMessage() }}</p>
      }

      @if (evaluation(); as e) {
        <div class="space-y-2">
          @if (e.cached) {
            <p class="text-xs" style="color: var(--text-muted)">Showing saved evaluation (unchanged content).</p>
          }
          @if (e.truncated && e.truncation_note) {
            <p class="text-xs" style="color: var(--text-muted)">{{ e.truncation_note }}</p>
          }

          <div class="flex items-baseline gap-2">
            <span class="text-2xl font-semibold" style="color: var(--text)">{{ e.overall_score }}</span>
            <span class="text-xs" style="color: var(--text-muted)">Overall · {{ e.provider }} / {{ e.model }}</span>
          </div>

          @if (e.already_strong) {
            <p class="text-xs" style="color: var(--success)">
              ✓ Your writing is already strong. No major changes are required.
            </p>
          }

          <div class="grid grid-cols-2 sm:grid-cols-3 gap-1">
            @for (entry of dimensionEntries(e); track entry[0]) {
              <div class="text-xs flex justify-between gap-2 border-b border-[var(--border)] py-0.5">
                <span style="color: var(--text-muted)">{{ labelFor(entry[0]) }}</span>
                <span style="color: var(--text)">{{ entry[1] }}</span>
              </div>
            }
          </div>

          @if (e.strengths.length) {
            <div>
              <p class="text-xs font-medium mb-1">Strengths</p>
              <ul class="list-disc pl-4 text-xs space-y-0.5" style="color: var(--text-muted)">
                @for (s of e.strengths; track s) {
                  <li>{{ s }}</li>
                }
              </ul>
            </div>
          }

          @if (!e.already_strong && e.issues.length) {
            <div>
              <p class="text-xs font-medium mb-1">Priority improvements</p>
              <ul class="list-disc pl-4 text-xs space-y-1" style="color: var(--text-muted)">
                @for (issue of e.issues.slice(0, 5); track $index) {
                  <li>
                    <span class="font-medium" style="color: var(--text)">{{ issue.problem_type || 'Issue' }}</span>
                    @if (issue.explanation) {
                      — {{ issue.explanation }}
                    }
                  </li>
                }
              </ul>
            </div>
          }

          <button type="button" class="btn-secondary text-xs" (click)="showDetail.set(!showDetail())">
            {{ showDetail() ? 'Hide detailed feedback' : 'View detailed feedback' }}
          </button>

          @if (showDetail()) {
            <div class="space-y-2 border-t border-[var(--border)] pt-2">
              @if (e.suggestions.length) {
                <div>
                  <p class="text-xs font-medium mb-1">Suggestions</p>
                  <ul class="list-disc pl-4 text-xs space-y-0.5" style="color: var(--text-muted)">
                    @for (s of e.suggestions; track s) {
                      <li>{{ s }}</li>
                    }
                  </ul>
                </div>
              }
              @for (issue of e.issues; track $index) {
                <div class="text-xs space-y-0.5 p-2" style="background: var(--surface-2, transparent)">
                  <p class="font-medium" style="color: var(--text)">
                    {{ issue.problem_type || 'Issue' }}
                    <span style="color: var(--text-muted)">({{ issue.severity }})</span>
                  </p>
                  @if (issue.original_text) {
                    <p style="color: var(--text-muted)">“{{ issue.original_text }}”</p>
                  }
                  @if (issue.explanation) {
                    <p>{{ issue.explanation }}</p>
                  }
                  @if (issue.suggestion) {
                    <p style="color: var(--success)">Suggestion: {{ issue.suggestion }}</p>
                  }
                </div>
              }
              @if (e.metrics && metricEntries(e).length) {
                <div>
                  <p class="text-xs font-medium mb-1">Deterministic metrics</p>
                  <div class="grid grid-cols-2 gap-1 text-xs" style="color: var(--text-muted)">
                    @for (m of metricEntries(e); track m[0]) {
                      <div class="flex justify-between gap-2">
                        <span>{{ m[0] }}</span>
                        <span>{{ m[1] }}</span>
                      </div>
                    }
                  </div>
                </div>
              }
            </div>
          }
        </div>
      } @else if (!busy() && !errorMessage()) {
        <p class="text-xs" style="color: var(--text-muted)">
          Evaluate this writing with your connected Sarvam model. Feedback is stored and not re-billed for unchanged content.
        </p>
      }
    </div>
  `,
})
export class WritingFeedbackPanelComponent implements OnInit {
  private readonly communication = inject(CommunicationService);

  @Input({ required: true }) writingId!: string;

  readonly evaluation = signal<WritingEvaluation | null>(null);
  readonly busy = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly errorCode = signal<string | null>(null);
  readonly showDetail = signal(false);

  labelFor(key: string): string {
    return DIMENSION_LABELS[key] || key;
  }

  dimensionEntries(e: WritingEvaluation): [string, number][] {
    return Object.entries(e.dimensions || {});
  }

  metricEntries(e: WritingEvaluation): [string, number][] {
    return Object.entries(e.metrics || {}).slice(0, 12);
  }

  ngOnInit(): void {
    if (!this.writingId) return;
    this.communication.getAiFeedback(this.writingId).subscribe({
      next: (e) => this.evaluation.set(e),
      error: () => {
        /* no prior feedback is fine */
      },
    });
  }

  runFeedback(): void {
    if (!this.writingId || this.busy()) return;
    this.busy.set(true);
    this.errorMessage.set(null);
    this.errorCode.set(null);
    this.communication.requestAiFeedback(this.writingId).subscribe({
      next: (e) => {
        this.evaluation.set(e);
        this.busy.set(false);
      },
      error: (err) => {
        this.busy.set(false);
        const detail = err?.error?.detail;
        if (detail && typeof detail === 'object') {
          this.errorCode.set(detail.code || null);
          this.errorMessage.set(detail.message || 'AI feedback failed');
        } else if (typeof detail === 'string') {
          this.errorMessage.set(detail);
          if (detail.toLowerCase().includes('sarvam') || detail.toLowerCase().includes('api key')) {
            this.errorCode.set('missing_credential');
          }
        } else {
          this.errorMessage.set('AI feedback is temporarily unavailable. Your writing has not been changed.');
        }
      },
    });
  }
}
