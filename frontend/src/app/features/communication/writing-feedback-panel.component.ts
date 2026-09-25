import { Component, Input, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  DIMENSION_LABELS,
  WritingEvaluation,
  WritingRewrite,
} from './models/communication.models';
import { CommunicationService } from './services/communication.service';

type FeedbackTab = 'overview' | 'issues' | 'coach';

@Component({
  selector: 'app-writing-feedback-panel',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="panel text-sm feedback-panel">
      <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
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
        <div class="text-xs space-y-1 mb-2" style="color: var(--danger)">
          <p>{{ errorMessage() }}</p>
          <a routerLink="/integrations" class="link">Open Integrations → AI Integration</a>
        </div>
      } @else if (errorMessage()) {
        <p class="text-xs mb-2" style="color: var(--danger)">{{ errorMessage() }}</p>
      }

      @if (evaluation(); as e) {
        @if (e.cached) {
          <p class="text-xs mb-2" style="color: var(--text-muted)">Showing saved evaluation (unchanged content).</p>
        }
        @if (e.truncated && e.truncation_note) {
          <p class="text-xs mb-2" style="color: var(--text-muted)">{{ e.truncation_note }}</p>
        }

        <div class="tab-row">
          <button type="button" class="tab-btn" [class.tab-btn--active]="activeTab() === 'overview'" (click)="activeTab.set('overview')">
            Overview
          </button>
          <button type="button" class="tab-btn" [class.tab-btn--active]="activeTab() === 'issues'" (click)="activeTab.set('issues')">
            Issues
            @if (e.issues.length) {
              <span class="tab-badge">{{ e.issues.length }}</span>
            }
          </button>
          <button type="button" class="tab-btn" [class.tab-btn--active]="activeTab() === 'coach'" (click)="activeTab.set('coach')">
            Coach rewrite
          </button>
        </div>

        @if (activeTab() === 'overview') {
          <div class="tab-panel space-y-3">
            <div class="score-row">
              <div class="score-ring" [attr.data-score]="scoreBand(e.overall_score)">
                <span class="score-value">{{ e.overall_score }}</span>
              </div>
              <div class="min-w-0">
                <p class="font-medium" style="color: var(--text)">Overall score</p>
                <p class="text-xs" style="color: var(--text-muted)">{{ e.provider }} / {{ e.model }}</p>
                @if (e.already_strong) {
                  <p class="text-xs mt-1" style="color: var(--success)">
                    ✓ Already strong — no major changes needed.
                  </p>
                }
              </div>
            </div>

            <div class="dimension-list">
              @for (entry of topDimensions(e); track entry[0]) {
                <div class="dimension-row">
                  <div class="flex justify-between gap-2 text-xs mb-0.5">
                    <span style="color: var(--text-muted)">{{ labelFor(entry[0]) }}</span>
                    <span style="color: var(--text)">{{ entry[1] }}</span>
                  </div>
                  <div class="dimension-bar">
                    <div class="dimension-bar-fill" [style.width.%]="entry[1]"></div>
                  </div>
                </div>
              }
            </div>

            @if (e.strengths.length) {
              <div>
                <p class="text-xs font-medium mb-1">Strengths</p>
                <ul class="chip-list">
                  @for (s of e.strengths.slice(0, 4); track s) {
                    <li class="chip chip--good">{{ s }}</li>
                  }
                </ul>
              </div>
            }

            @if (!e.already_strong && e.issues.length) {
              <div>
                <p class="text-xs font-medium mb-1">Top fixes</p>
                <ul class="text-xs space-y-1" style="color: var(--text-muted)">
                  @for (issue of e.issues.slice(0, 3); track $index) {
                    <li>
                      <button type="button" class="issue-link" (click)="openIssue($index)">
                        {{ issue.problem_type || 'Issue' }} — {{ issue.explanation || issue.suggestion }}
                      </button>
                    </li>
                  }
                </ul>
              </div>
            }

            @if (e.suggestions.length) {
              <div>
                <p class="text-xs font-medium mb-1">Quick tips</p>
                <ul class="list-disc pl-4 text-xs space-y-0.5" style="color: var(--text-muted)">
                  @for (s of e.suggestions.slice(0, 3); track s) {
                    <li>{{ s }}</li>
                  }
                </ul>
              </div>
            }
          </div>
        }

        @if (activeTab() === 'issues') {
          <div class="tab-panel space-y-2">
            @if (!e.issues.length) {
              <p class="text-xs" style="color: var(--text-muted)">No issues flagged. Nice work.</p>
            }
            @for (issue of e.issues; track $index) {
              <details class="issue-card" [attr.open]="expandedIssue() === $index ? true : null">
                <summary class="issue-summary">
                  <span class="severity-badge" [attr.data-severity]="issue.severity">{{ issue.severity }}</span>
                  <span class="font-medium" style="color: var(--text)">{{ issue.problem_type || 'Issue' }}</span>
                </summary>
                <div class="issue-body text-xs space-y-1">
                  @if (issue.original_text) {
                    <p class="quote-line">“{{ issue.original_text }}”</p>
                  }
                  @if (issue.explanation) {
                    <p>{{ issue.explanation }}</p>
                  }
                  @if (issue.suggestion) {
                    <p class="suggestion-line">Try: {{ issue.suggestion }}</p>
                  }
                </div>
              </details>
            }

            @if (e.metrics && metricEntries(e).length) {
              <details class="text-xs">
                <summary class="cursor-pointer font-medium mb-1" style="color: var(--text)">Deterministic metrics</summary>
                <div class="grid grid-cols-2 gap-1 mt-1" style="color: var(--text-muted)">
                  @for (m of metricEntries(e); track m[0]) {
                    <div class="flex justify-between gap-2">
                      <span>{{ m[0] }}</span>
                      <span>{{ m[1] }}</span>
                    </div>
                  }
                </div>
              </details>
            }
          </div>
        }

        @if (activeTab() === 'coach') {
          <div class="tab-panel space-y-3">
            <p class="text-xs" style="color: var(--text-muted)">
              See how the coach would write your paragraph — your original stays unchanged.
            </p>

            <button
              type="button"
              class="btn-secondary text-xs w-full sm:w-auto"
              [disabled]="rewriteBusy() || !writingId"
              (click)="runRewrite()"
            >
              {{ rewriteBusy() ? 'Generating…' : 'How AI would write this' }}
            </button>

            @if (rewriteError()) {
              <p class="text-xs" style="color: var(--danger)">{{ rewriteError() }}</p>
            }

            @if (rewrite(); as r) {
              @if (r.cached) {
                <p class="text-xs" style="color: var(--text-muted)">Showing saved rewrite (unchanged content).</p>
              }
              @if (r.truncated && r.truncation_note) {
                <p class="text-xs" style="color: var(--text-muted)">{{ r.truncation_note }}</p>
              }

              <div class="compare-grid">
                <div class="compare-col">
                  <p class="compare-label">Your version</p>
                  <div class="compare-body">{{ originalContent || '—' }}</div>
                </div>
                <div class="compare-col compare-col--coach">
                  <p class="compare-label">Coach version</p>
                  <div class="compare-body">{{ r.suggested_text }}</div>
                </div>
              </div>

              @if (r.why_better.length) {
                <div>
                  <p class="text-xs font-medium mb-1">Why this works better</p>
                  <ul class="list-disc pl-4 text-xs space-y-0.5" style="color: var(--text-muted)">
                    @for (w of r.why_better; track w) {
                      <li>{{ w }}</li>
                    }
                  </ul>
                </div>
              }

              @if (r.key_changes.length) {
                <div>
                  <p class="text-xs font-medium mb-1">Key changes</p>
                  <ul class="list-disc pl-4 text-xs space-y-0.5" style="color: var(--text-muted)">
                    @for (c of r.key_changes; track c) {
                      <li>{{ c }}</li>
                    }
                  </ul>
                </div>
              }
            }
          </div>
        }
      } @else if (!busy() && !errorMessage()) {
        <p class="text-xs" style="color: var(--text-muted)">
          Evaluate this writing with the AI model assigned to Writing Feedback. Feedback is stored and not re-billed for unchanged content.
        </p>
      }
    </div>
  `,
  styles: [
    `
      .feedback-panel {
        display: flex;
        flex-direction: column;
        min-height: 12rem;
      }

      .tab-row {
        display: flex;
        gap: 0.25rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 0.75rem;
        overflow-x: auto;
      }

      .tab-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.45rem 0.65rem;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-muted);
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        cursor: pointer;
        margin-bottom: -1px;
        white-space: nowrap;
      }

      .tab-btn:hover {
        color: var(--text);
      }

      .tab-btn--active {
        color: var(--primary) !important;
        border-bottom-color: var(--primary) !important;
        font-weight: 600;
      }

      .tab-badge {
        font-size: 0.65rem;
        padding: 0.05rem 0.35rem;
        border-radius: 999px;
        background: var(--surface-2, rgba(0, 0, 0, 0.06));
        color: var(--text-muted);
      }

      .tab-panel {
        flex: 1;
        min-height: 0;
      }

      .score-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
      }

      .score-ring {
        width: 3.5rem;
        height: 3.5rem;
        border-radius: 999px;
        display: grid;
        place-items: center;
        border: 3px solid var(--border);
        flex-shrink: 0;
      }

      .score-ring[data-score='high'] {
        border-color: var(--success);
      }

      .score-ring[data-score='mid'] {
        border-color: var(--primary);
      }

      .score-ring[data-score='low'] {
        border-color: var(--danger);
      }

      .score-value {
        font-size: 1.125rem;
        font-weight: 700;
        color: var(--text);
      }

      .dimension-list {
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
      }

      .dimension-bar {
        height: 0.35rem;
        border-radius: 999px;
        background: var(--surface-2, rgba(0, 0, 0, 0.06));
        overflow: hidden;
      }

      .dimension-bar-fill {
        height: 100%;
        border-radius: inherit;
        background: var(--primary);
      }

      .chip-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
      }

      .chip {
        font-size: 0.7rem;
        padding: 0.2rem 0.45rem;
        border-radius: 0.25rem;
        border: 1px solid var(--border);
        color: var(--text-muted);
      }

      .chip--good {
        border-color: color-mix(in srgb, var(--success) 35%, var(--border));
        color: var(--text);
      }

      .issue-link {
        text-align: left;
        background: none;
        border: none;
        padding: 0;
        color: inherit;
        cursor: pointer;
        text-decoration: underline;
        text-underline-offset: 2px;
      }

      .issue-card {
        border: 1px solid var(--border);
        border-radius: 0.35rem;
        padding: 0.35rem 0.5rem;
      }

      .issue-summary {
        cursor: pointer;
        list-style: none;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .issue-summary::-webkit-details-marker {
        display: none;
      }

      .severity-badge {
        font-size: 0.65rem;
        text-transform: uppercase;
        padding: 0.1rem 0.35rem;
        border-radius: 0.2rem;
        background: var(--surface-2, rgba(0, 0, 0, 0.06));
        color: var(--text-muted);
      }

      .severity-badge[data-severity='high'] {
        color: var(--danger);
      }

      .severity-badge[data-severity='medium'] {
        color: var(--primary);
      }

      .issue-body {
        margin-top: 0.35rem;
        padding-top: 0.35rem;
        border-top: 1px solid var(--border);
        color: var(--text-muted);
      }

      .quote-line {
        font-style: italic;
      }

      .suggestion-line {
        color: var(--success);
      }

      .compare-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.5rem;
      }

      @media (min-width: 640px) {
        .compare-grid {
          grid-template-columns: 1fr 1fr;
        }
      }

      .compare-col {
        border: 1px solid var(--border);
        border-radius: 0.35rem;
        overflow: hidden;
      }

      .compare-col--coach {
        border-color: color-mix(in srgb, var(--primary) 40%, var(--border));
      }

      .compare-label {
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        padding: 0.35rem 0.5rem;
        margin: 0;
        background: var(--surface-2, rgba(0, 0, 0, 0.04));
        color: var(--text-muted);
      }

      .compare-body {
        padding: 0.5rem;
        font-size: 0.75rem;
        line-height: 1.45;
        color: var(--text);
        white-space: pre-wrap;
        max-height: 14rem;
        overflow-y: auto;
      }
    `,
  ],
})
export class WritingFeedbackPanelComponent implements OnInit {
  private readonly communication = inject(CommunicationService);

  @Input({ required: true }) writingId!: string;
  @Input() originalContent = '';

  readonly evaluation = signal<WritingEvaluation | null>(null);
  readonly rewrite = signal<WritingRewrite | null>(null);
  readonly busy = signal(false);
  readonly rewriteBusy = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly errorCode = signal<string | null>(null);
  readonly rewriteError = signal<string | null>(null);
  readonly activeTab = signal<FeedbackTab>('overview');
  readonly expandedIssue = signal<number | null>(null);

  labelFor(key: string): string {
    return DIMENSION_LABELS[key] || key;
  }

  scoreBand(score: number): 'high' | 'mid' | 'low' {
    if (score >= 85) return 'high';
    if (score >= 70) return 'mid';
    return 'low';
  }

  topDimensions(e: WritingEvaluation): [string, number][] {
    return Object.entries(e.dimensions || {})
      .sort((a, b) => a[1] - b[1])
      .slice(0, 6);
  }

  metricEntries(e: WritingEvaluation): [string, number][] {
    return Object.entries(e.metrics || {}).slice(0, 12);
  }

  openIssue(index: number): void {
    this.expandedIssue.set(index);
    this.activeTab.set('issues');
  }

  ngOnInit(): void {
    if (!this.writingId) return;
    this.communication.getAiFeedback(this.writingId).subscribe({
      next: (e) => this.evaluation.set(e),
      error: () => {
        /* no prior feedback is fine */
      },
    });
    this.communication.getAiRewrite(this.writingId).subscribe({
      next: (r) => this.rewrite.set(r),
      error: () => {
        /* no prior rewrite is fine */
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
        this.activeTab.set('overview');
      },
      error: (err) => this.handleFeedbackError(err),
    });
  }

  runRewrite(): void {
    if (!this.writingId || this.rewriteBusy()) return;
    this.rewriteBusy.set(true);
    this.rewriteError.set(null);
    this.communication.requestAiRewrite(this.writingId).subscribe({
      next: (r) => {
        this.rewrite.set(r);
        this.rewriteBusy.set(false);
        this.activeTab.set('coach');
      },
      error: (err) => {
        this.rewriteBusy.set(false);
        const detail = err?.error?.detail;
        if (detail && typeof detail === 'object') {
          this.rewriteError.set(detail.message || 'Coach rewrite failed');
        } else if (typeof detail === 'string') {
          this.rewriteError.set(detail);
        } else {
          this.rewriteError.set('Coach rewrite is temporarily unavailable. Your writing has not been changed.');
        }
      },
    });
  }

  private handleFeedbackError(err: { error?: { detail?: unknown } }): void {
    this.busy.set(false);
    const detail = err?.error?.detail;
    if (detail && typeof detail === 'object') {
      const d = detail as { code?: string; message?: string };
      this.errorCode.set(d.code || null);
      this.errorMessage.set(d.message || 'AI feedback failed');
    } else if (typeof detail === 'string') {
      this.errorMessage.set(detail);
    } else {
      this.errorMessage.set('AI feedback is temporarily unavailable. Your writing has not been changed.');
    }
  }
}
