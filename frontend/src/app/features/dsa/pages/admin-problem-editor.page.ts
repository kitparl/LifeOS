import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { ThemeService } from '../../../core/services/theme.service';
import { MarkdownPreviewComponent } from '../../../shared/code-workspace/components/markdown-preview/markdown-preview.component';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { DsaStateComponent } from '../components/dsa-state.component';
import {
  AdminProblemDetail,
  AdminTestCase,
  CaseWrite,
  CompareMode,
  Difficulty,
  JsonValue,
  ProblemStatus,
  ProblemUpdate,
  SignatureSpec,
  formatJson,
} from '../models/dsa.models';
import { DsaService } from '../services/dsa.service';

interface ProblemForm {
  title: string;
  difficulty: Difficulty;
  status: ProblemStatus;
  is_variant: boolean;
  tags: string;
  statement: string;
  constraints: string;
  signature: string;
  compare_mode: CompareMode;
  checker: string;
  time_limit_ms: number;
  memory_limit_mb: number;
}

interface CaseForm {
  id: string | null;
  input: string;
  expected: string;
  is_sample: boolean;
  explanation: string;
}

const COMPARE_MODES: CompareMode[] = ['exact', 'unordered', 'unordered_nested', 'float_tolerance', 'checker'];

export function serverMessage(err: unknown): string {
  if (err instanceof HttpErrorResponse) {
    const detail = (err.error as { detail?: unknown } | null)?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { loc?: unknown[]; msg?: string };
      return `${(first.loc ?? []).slice(1).join('.')}: ${first.msg ?? 'invalid value'}`;
    }
    if (err.status === 403) return 'Admin access is required.';
  }
  return 'Something went wrong. Please try again.';
}

function toForm(p: AdminProblemDetail): ProblemForm {
  return {
    title: p.title,
    difficulty: p.difficulty,
    status: p.status,
    is_variant: p.is_variant,
    tags: p.tags.join(', '),
    statement: p.statement,
    constraints: p.constraints,
    signature: p.signature ? JSON.stringify(p.signature, null, 2) : '',
    compare_mode: p.compare_mode,
    checker: p.checker ?? '',
    time_limit_ms: p.time_limit_ms,
    memory_limit_mb: p.memory_limit_mb,
  };
}

/** Only the fields that differ from the loaded problem; throws on invalid signature JSON. */
export function problemChanges(p: AdminProblemDetail, f: ProblemForm): ProblemUpdate {
  const update: ProblemUpdate = {};
  const tags = f.tags.split(',').map((t) => t.trim()).filter(Boolean);
  if (f.title !== p.title) update.title = f.title;
  if (f.difficulty !== p.difficulty) update.difficulty = f.difficulty;
  if (f.status !== p.status) update.status = f.status;
  if (f.is_variant !== p.is_variant) update.is_variant = f.is_variant;
  if (tags.join(',') !== p.tags.join(',')) update.tags = tags;
  if (f.statement !== p.statement) update.statement = f.statement;
  if (f.constraints !== p.constraints) update.constraints = f.constraints;
  if (f.compare_mode !== p.compare_mode) update.compare_mode = f.compare_mode;
  if ((f.checker || null) !== p.checker) update.checker = f.checker || null;
  if (f.time_limit_ms !== p.time_limit_ms) update.time_limit_ms = f.time_limit_ms;
  if (f.memory_limit_mb !== p.memory_limit_mb) update.memory_limit_mb = f.memory_limit_mb;
  const signature = f.signature.trim() ? (JSON.parse(f.signature) as SignatureSpec) : null;
  if (JSON.stringify(signature) !== JSON.stringify(p.signature)) update.signature = signature;
  return update;
}

@Component({
  selector: 'app-dsa-admin-problem-editor-page',
  standalone: true,
  imports: [FormsModule, RouterLink, LucideDynamicIcon, MarkdownPreviewComponent, DsaStateComponent],
  template: `
    <div class="mx-auto max-w-5xl space-y-4">
      <a class="btn-ghost !min-h-8 !px-2 text-xs" [routerLink]="['../../../problems', slug]" data-testid="dsa-admin-back-link">
        <svg class="h-3.5 w-3.5" lucideIcon="chevron-left" aria-hidden="true"></svg>
        Back to problem
      </a>

      @if (loading()) {
        <div class="panel skeleton h-96"></div>
      } @else if (loadError()) {
        <app-dsa-state title="We couldn't load this problem." [message]="loadError()" [retryable]="true" (retry)="load()" />
      } @else if (problem()) {
        @let p = problem()!;
        <header class="flex flex-wrap items-center gap-2">
          <h1 class="text-xl font-semibold">Edit: {{ p.title }}</h1>
          @if (p.edited_in_ui) {
            <span class="badge badge--info" title="The seeder will not overwrite this problem unless run with --force">Edited in UI</span>
          }
        </header>

        <form class="panel space-y-3" (ngSubmit)="save()" data-testid="dsa-admin-problem-form">
          <div class="grid gap-3 sm:grid-cols-2">
            <label class="block space-y-1">
              <span class="form-label">Title</span>
              <input class="input-field" name="title" [(ngModel)]="form.title" required maxlength="200" data-testid="dsa-admin-title-input" />
            </label>
            <label class="block space-y-1">
              <span class="form-label">Tags (comma separated)</span>
              <input class="input-field" name="tags" [(ngModel)]="form.tags" data-testid="dsa-admin-tags-input" />
            </label>
            <label class="block space-y-1">
              <span class="form-label">Difficulty</span>
              <select class="input-field" name="difficulty" [(ngModel)]="form.difficulty" data-testid="dsa-admin-difficulty-select">
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </label>
            <label class="block space-y-1">
              <span class="form-label">Status</span>
              <select class="input-field" name="status" [(ngModel)]="form.status" data-testid="dsa-admin-status-select">
                <option value="draft">Draft (coming soon)</option>
                <option value="published">Published</option>
              </select>
            </label>
            <label class="block space-y-1">
              <span class="form-label">Compare mode</span>
              <select class="input-field" name="compare_mode" [(ngModel)]="form.compare_mode" data-testid="dsa-admin-compare-select">
                @for (m of compareModes; track m) {
                  <option [value]="m">{{ m }}</option>
                }
              </select>
            </label>
            <label class="block space-y-1">
              <span class="form-label">Checker (compare mode "checker" only)</span>
              <input class="input-field" name="checker" [(ngModel)]="form.checker" maxlength="60" data-testid="dsa-admin-checker-input" />
            </label>
            <label class="block space-y-1">
              <span class="form-label">Time limit per test (ms)</span>
              <input class="input-field" type="number" name="time" min="100" max="5000" [(ngModel)]="form.time_limit_ms" data-testid="dsa-admin-time-input" />
            </label>
            <label class="block space-y-1">
              <span class="form-label">Memory limit (MB)</span>
              <input class="input-field" type="number" name="memory" min="32" max="512" [(ngModel)]="form.memory_limit_mb" data-testid="dsa-admin-memory-input" />
            </label>
          </div>
          <label class="flex items-center gap-2 text-sm">
            <input type="checkbox" name="variant" [(ngModel)]="form.is_variant" data-testid="dsa-admin-variant-checkbox" />
            Variant (our own definition of a course-specific title)
          </label>

          <div class="flex items-center justify-between">
            <span class="form-label">Statement (markdown)</span>
            <button type="button" class="btn-ghost !min-h-8 !px-2 text-xs" data-testid="dsa-admin-preview-toggle" (click)="preview.set(!preview())">
              {{ preview() ? 'Edit' : 'Preview' }}
            </button>
          </div>
          @if (preview()) {
            <div class="panel--flat">
              <app-markdown-preview [content]="form.statement" [theme]="theme()" />
              <h3 class="section-heading mt-3">Constraints</h3>
              <app-markdown-preview [content]="form.constraints" [theme]="theme()" />
            </div>
          } @else {
            <textarea class="input-field font-mono text-xs" rows="10" name="statement" [(ngModel)]="form.statement" data-testid="dsa-admin-statement-input"></textarea>
            <label class="block space-y-1">
              <span class="form-label">Constraints (markdown)</span>
              <textarea class="input-field font-mono text-xs" rows="4" name="constraints" [(ngModel)]="form.constraints" data-testid="dsa-admin-constraints-input"></textarea>
            </label>
          }
          <label class="block space-y-1">
            <span class="form-label">Signature (JSON)</span>
            <textarea class="input-field font-mono text-xs" rows="8" name="signature" [(ngModel)]="form.signature" data-testid="dsa-admin-signature-input"></textarea>
          </label>

          @if (saveError()) {
            <p class="text-sm" role="alert" style="color: var(--danger)" data-testid="dsa-admin-save-error">{{ saveError() }}</p>
          }
          @if (saved()) {
            <p class="text-sm" role="status" style="color: var(--success)">Saved.</p>
          }
          <button type="submit" class="btn-primary" [disabled]="saving()" data-testid="dsa-admin-save-button">
            {{ saving() ? 'Saving…' : 'Save problem' }}
          </button>
        </form>

        <section class="panel space-y-3" aria-label="Test cases">
          <div class="flex items-center justify-between">
            <h2 class="section-heading">Test cases ({{ p.tests.length }})</h2>
            <button type="button" class="btn-secondary !min-h-8 !px-2.5 text-xs" data-testid="dsa-admin-test-add-button"
              [disabled]="!p.signature" (click)="editCase(null)">
              <svg class="h-3.5 w-3.5" lucideIcon="plus" aria-hidden="true"></svg>
              Add test
            </button>
          </div>
          @if (!p.signature) {
            <p class="text-xs" style="color: var(--text-muted)">Save a signature before adding tests.</p>
          }

          @if (caseForm(); as c) {
            <form class="panel--flat space-y-2" (ngSubmit)="saveCase()" data-testid="dsa-admin-case-form">
              <label class="block space-y-1">
                <span class="form-label">Input (JSON)</span>
                <textarea class="input-field font-mono text-xs" rows="3" name="case-input" [(ngModel)]="c.input" data-testid="dsa-admin-case-input"></textarea>
              </label>
              <label class="block space-y-1">
                <span class="form-label">Expected output (JSON)</span>
                <textarea class="input-field font-mono text-xs" rows="2" name="case-expected" [(ngModel)]="c.expected" data-testid="dsa-admin-case-expected"></textarea>
              </label>
              <label class="flex items-center gap-2 text-sm">
                <input type="checkbox" name="case-sample" [(ngModel)]="c.is_sample" data-testid="dsa-admin-case-sample" />
                Sample (shown to users as an example)
              </label>
              @if (c.is_sample) {
                <label class="block space-y-1">
                  <span class="form-label">Explanation</span>
                  <input class="input-field" name="case-explanation" [(ngModel)]="c.explanation" maxlength="2000" data-testid="dsa-admin-case-explanation" />
                </label>
              }
              @if (caseError()) {
                <p class="text-sm" role="alert" style="color: var(--danger)" data-testid="dsa-admin-case-error">{{ caseError() }}</p>
              }
              <div class="flex gap-2">
                <button type="submit" class="btn-primary !min-h-8 !px-3 text-xs" data-testid="dsa-admin-case-save-button">Save test</button>
                <button type="button" class="btn-ghost !min-h-8 !px-3 text-xs" data-testid="dsa-admin-case-cancel-button" (click)="caseForm.set(null)">Cancel</button>
              </div>
            </form>
          }

          <ul class="space-y-1.5">
            @for (t of p.tests; track t.id) {
              <li class="panel--flat flex flex-wrap items-start gap-2 !p-2.5 text-xs" [attr.data-testid]="'dsa-admin-test-' + t.position">
                <span class="font-medium">#{{ t.position }}</span>
                <span class="badge" [class.badge--primary]="t.is_sample" [class.badge--default]="!t.is_sample">{{ t.is_sample ? 'sample' : t.kind }}</span>
                <code class="min-w-0 flex-1 break-all">{{ json(t.input) }} → {{ json(t.expected) }}</code>
                <button type="button" class="btn-ghost !min-h-7 !px-2" [attr.data-testid]="'dsa-admin-test-edit-' + t.position" (click)="editCase(t)" aria-label="Edit test">
                  <svg class="h-3.5 w-3.5" lucideIcon="pencil" aria-hidden="true"></svg>
                </button>
                <button type="button" class="btn-ghost !min-h-7 !px-2" [attr.data-testid]="'dsa-admin-test-delete-' + t.position" (click)="deleteCase(t)" aria-label="Delete test">
                  <svg class="h-3.5 w-3.5" lucideIcon="trash-2" aria-hidden="true"></svg>
                </button>
              </li>
            }
          </ul>
        </section>
      }
    </div>
  `,
})
export class AdminProblemEditorPageComponent implements OnInit {
  private readonly dsa = inject(DsaService);
  private readonly route = inject(ActivatedRoute);
  private readonly confirm = inject(ConfirmService);
  readonly theme = inject(ThemeService).resolved;

  readonly compareModes = COMPARE_MODES;
  readonly json = formatJson;
  readonly slug = this.route.snapshot.paramMap.get('slug') ?? '';

  readonly problem = signal<AdminProblemDetail | null>(null);
  readonly loading = signal(true);
  readonly loadError = signal<string | null>(null);
  readonly saving = signal(false);
  readonly saved = signal(false);
  readonly saveError = signal<string | null>(null);
  readonly preview = signal(false);
  readonly caseForm = signal<CaseForm | null>(null);
  readonly caseError = signal<string | null>(null);
  form!: ProblemForm;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.loadError.set(null);
    this.dsa.adminProblem(this.slug).subscribe({
      next: (p) => this.setProblem(p),
      error: (err: unknown) => {
        this.loadError.set(serverMessage(err));
        this.loading.set(false);
      },
    });
  }

  private setProblem(p: AdminProblemDetail): void {
    this.form = toForm(p);
    this.problem.set(p);
    this.loading.set(false);
  }

  save(): void {
    const p = this.problem();
    if (!p) return;
    this.saved.set(false);
    this.saveError.set(null);
    let update: ProblemUpdate;
    try {
      update = problemChanges(p, this.form);
    } catch {
      this.saveError.set('The signature is not valid JSON.');
      return;
    }
    if (Object.keys(update).length === 0) {
      this.saved.set(true);
      return;
    }
    this.saving.set(true);
    this.dsa.adminUpdateProblem(this.slug, update).subscribe({
      next: (updated) => {
        this.setProblem(updated);
        this.saving.set(false);
        this.saved.set(true);
      },
      error: (err: unknown) => {
        this.saveError.set(serverMessage(err));
        this.saving.set(false);
      },
    });
  }

  editCase(test: AdminTestCase | null): void {
    this.caseError.set(null);
    this.caseForm.set(
      test
        ? { id: test.id, input: this.json(test.input), expected: this.json(test.expected), is_sample: test.is_sample, explanation: test.explanation ?? '' }
        : { id: null, input: '', expected: '', is_sample: false, explanation: '' },
    );
  }

  saveCase(): void {
    const c = this.caseForm();
    if (!c) return;
    let body: CaseWrite;
    try {
      body = {
        input: JSON.parse(c.input) as JsonValue,
        expected: JSON.parse(c.expected) as JsonValue,
        is_sample: c.is_sample,
        explanation: c.is_sample && c.explanation.trim() ? c.explanation.trim() : null,
      };
    } catch {
      this.caseError.set('Input and expected output must be valid JSON.');
      return;
    }
    const request = c.id ? this.dsa.adminUpdateTest(c.id, body) : this.dsa.adminAddTest(this.slug, body);
    request.subscribe({
      next: () => {
        this.caseForm.set(null);
        this.load();
      },
      error: (err: unknown) => this.caseError.set(serverMessage(err)),
    });
  }

  async deleteCase(test: AdminTestCase): Promise<void> {
    const ok = await this.confirm.confirm(`Delete test #${test.position}?`, 'Delete test');
    if (!ok) return;
    this.dsa.adminDeleteTest(test.id).subscribe({
      next: () => this.load(),
      error: (err: unknown) => this.saveError.set(serverMessage(err)),
    });
  }
}
