import { HttpErrorResponse } from '@angular/common/http';
import { Component, ElementRef, OnDestroy, OnInit, ViewChild, computed, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { Subscription } from 'rxjs';
import { ThemeService } from '../../../core/services/theme.service';
import { MarkdownEditorComponent } from '../../../shared/code-workspace/components/markdown-editor/markdown-editor.component';
import { MarkdownPreviewComponent } from '../../../shared/code-workspace/components/markdown-preview/markdown-preview.component';
import { SplitBounds, SplitDividerComponent } from '../../../shared/split-divider/split-divider.component';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { DifficultyBadgeComponent } from '../components/difficulty-badge.component';
import { DsaStateComponent } from '../components/dsa-state.component';
import { DsaNoteEditorComponent } from '../components/dsa-note-editor.component';
import { ProgressIconComponent } from '../components/progress-icon.component';
import { RunResultsComponent } from '../components/run-results.component';
import { SubmissionHistoryComponent } from '../components/submission-history.component';
import { SubmissionResultComponent } from '../components/submission-result.component';
import { TestCasesComponent } from '../components/test-cases.component';
import { TestInputComponent } from '../components/test-input.component';
import {
  DsaLanguage,
  JsonValue,
  LANGUAGE_LABELS,
  MAX_RUN_CASES,
  MAX_RUN_INPUT_BYTES,
  ProblemDetail,
  RunResult,
  SubmissionDetail,
  formatJson,
  inputFields,
  isTerminal,
  joinInput,
  parseJson,
  splitInput,
} from '../models/dsa.models';
import { DsaDraftStore } from '../services/dsa-draft.store';
import { DsaPollTimeoutError, DsaService } from '../services/dsa.service';

type Tab = 'description' | 'submissions' | 'note';
type ConsoleTab = 'cases' | 'result';
type Action = 'run' | 'submit';

const DRAFT_SAVE_DELAY_MS = 1000;

/** Friendly text for Run/Submit failures (the judge's own verdicts are shown in the result panels). */
export function actionErrorMessage(err: unknown): string {
  if (err instanceof DsaPollTimeoutError) return err.message;
  if (err instanceof HttpErrorResponse) {
    if (err.status === 503) return "The judge isn't available on this server right now.";
    const detail = (err.error as { detail?: unknown } | null)?.detail;
    if ((err.status === 400 || err.status === 409 || err.status === 429) && typeof detail === 'string') return detail;
    if (err.status === 422) return 'Check your code and test cases, then try again.';
  }
  return 'Something went wrong. Please try again.';
}

@Component({
  selector: 'app-dsa-problem-detail-page',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    LucideDynamicIcon,
    MarkdownEditorComponent,
    MarkdownPreviewComponent,
    SplitDividerComponent,
    DifficultyBadgeComponent,
    DsaStateComponent,
    DsaNoteEditorComponent,
    ProgressIconComponent,
    RunResultsComponent,
    SubmissionHistoryComponent,
    SubmissionResultComponent,
    TestCasesComponent,
    TestInputComponent,
  ],
  template: `
    <div class="mx-auto max-w-7xl space-y-3">
      @if (loading()) {
        <div class="panel skeleton h-96"></div>
      } @else if (notFound()) {
        <app-dsa-state title="Problem not found" />
      } @else if (loadError()) {
        <app-dsa-state title="We couldn't load this problem." [retryable]="true" (retry)="load()" />
      } @else if (problem()) {
        @let p = problem()!;
        <div class="flex flex-wrap items-center gap-2">
          <a class="btn-ghost !min-h-8 !px-2 text-xs" [routerLink]="['../../patterns', p.pattern_slug]" data-testid="dsa-detail-back-link">
            <svg class="h-3.5 w-3.5" lucideIcon="chevron-left" aria-hidden="true"></svg>
            {{ p.pattern_name }}
          </a>
          @if (dsa.canEdit()) {
            <a class="btn-ghost !min-h-8 !px-2 text-xs ml-auto" [routerLink]="['../../admin/problems', p.slug]" data-testid="dsa-detail-edit-link">
              <svg class="h-3.5 w-3.5" lucideIcon="pencil" aria-hidden="true"></svg>
              Edit
            </a>
          }
        </div>

        <div class="grid gap-3 lg:gap-0 lg:[grid-template-columns:var(--dsa-cols)]" [style.--dsa-cols]="splitColumns()" #splitGrid>
          <!-- Left: description / submissions -->
          <section class="panel !p-0 flex min-h-0 flex-col lg:h-[calc(100vh-10rem)]">
            <div class="tab-bar px-2" role="tablist">
              <button type="button" role="tab" class="tab-bar__btn" [class.active]="tab() === 'description'"
                [attr.aria-selected]="tab() === 'description'" data-testid="dsa-detail-tab-description" (click)="tab.set('description')">
                Description
              </button>
              <button type="button" role="tab" class="tab-bar__btn" [class.active]="tab() === 'submissions'"
                [attr.aria-selected]="tab() === 'submissions'" data-testid="dsa-detail-tab-submissions" (click)="tab.set('submissions')">
                Submissions
              </button>
              <button type="button" role="tab" class="tab-bar__btn" [class.active]="tab() === 'note'"
                [attr.aria-selected]="tab() === 'note'" data-testid="dsa-detail-tab-note" (click)="tab.set('note')">
                Note
              </button>
            </div>
            <div class="min-h-0 flex-1 overflow-auto p-4">
              @if (tab() === 'description') {
                <div class="space-y-3">
                  <div class="flex flex-wrap items-center gap-2">
                    <h1 class="text-lg font-semibold">{{ p.title }}</h1>
                    <app-dsa-progress-icon [status]="p.progress" />
                  </div>
                  <div class="flex flex-wrap items-center gap-1.5">
                    <app-dsa-difficulty-badge [difficulty]="p.difficulty" />
                    @if (p.tags.includes('blind75')) {
                      <span class="chip !py-0 text-[0.6875rem]">B75</span>
                    }
                    @if (p.is_variant) {
                      <span class="chip !py-0 text-[0.6875rem]" title="Our own definition of a course-specific title">Variant</span>
                    }
                  </div>
                  @if (p.status === 'draft') {
                    <app-dsa-state title="Coming soon" message="This problem's statement and tests haven't been added yet." />
                  } @else {
                    <app-markdown-preview [content]="p.statement" [theme]="theme()" />
                    @for (s of p.samples; track $index) {
                      <div class="panel--flat space-y-1 !p-3 text-xs" [attr.data-testid]="'dsa-detail-example-' + $index">
                        <p class="font-medium">Example {{ $index + 1 }}</p>
                        <div style="color: var(--text-muted)">Input</div>
                        <app-dsa-test-input class="block pl-3" [signature]="p.signature" [value]="s.input" />
                        <div><span style="color: var(--text-muted)">Output</span> <code class="break-all">{{ json(s.expected) }}</code></div>
                        @if (s.explanation) {
                          <p style="color: var(--text-muted)">{{ s.explanation }}</p>
                        }
                      </div>
                    }
                    <h2 class="section-heading">Constraints</h2>
                    <app-markdown-preview [content]="p.constraints" [theme]="theme()" />
                    <p class="text-xs" style="color: var(--text-faint)">
                      Time limit {{ p.time_limit_ms }} ms per test (scaled per language) · Memory {{ p.memory_limit_mb }} MB
                    </p>
                  }
                </div>
              } @else if (tab() === 'note') {
                <app-dsa-note-editor scope="problems" [slug]="p.slug" />
              } @else {
                <app-dsa-submission-history [slug]="p.slug" [refresh]="historyVersion()" [theme]="theme()" [signature]="p.signature"
                  (loadCode)="loadIntoEditor($event)" (useAsTestCase)="useAsTestCase($event)" />
              }
            </div>
          </section>

          <!-- Resizable divider (desktop only) -->
          <app-split-divider
            class="relative mx-1 hidden w-1 cursor-col-resize bg-[var(--border)] hover:bg-[var(--primary)] focus-visible:bg-[var(--primary)] data-[resizing=true]:bg-[var(--primary)] lg:block"
            [value]="splitRatio()" [min]="splitMin" [max]="splitMax" [bounds]="splitBounds"
            label="Resize description and editor" data-testid="dsa-detail-divider"
            (valueChange)="setSplit($event)" />

          <!-- Right: editor + results -->
          <section class="flex min-h-0 flex-col gap-3 lg:h-[calc(100vh-10rem)]">
            @if (p.status === 'published') {
              <div class="panel !p-0 flex min-h-[22rem] flex-1 flex-col overflow-hidden">
                <div class="toolbar flex flex-wrap items-center gap-2 px-2 py-1.5" style="border-bottom: 1px solid var(--border)">
                  <label class="sr-only" for="dsa-language">Language</label>
                  <select id="dsa-language" class="input-field !w-auto !py-1 text-xs" data-testid="dsa-detail-language-select"
                    [ngModel]="language()" (ngModelChange)="changeLanguage($event)" [disabled]="busy() !== null">
                    @for (lang of p.languages; track lang) {
                      <option [value]="lang">{{ labels[lang] }}</option>
                    }
                  </select>
                  <button type="button" class="btn-ghost !min-h-8 !px-2 text-xs" data-testid="dsa-detail-reset-button"
                    [disabled]="busy() !== null" (click)="reset()">
                    <svg class="h-3.5 w-3.5" lucideIcon="rotate-ccw" aria-hidden="true"></svg>
                    Reset
                  </button>
                  <div class="ml-auto flex items-center gap-2">
                    <button type="button" class="btn-secondary !min-h-8 !px-3 text-xs" data-testid="dsa-detail-run-button"
                      [disabled]="busy() !== null" (click)="run()">
                      <svg class="h-3.5 w-3.5" lucideIcon="play" aria-hidden="true"></svg>
                      {{ busy() === 'run' ? 'Running…' : 'Run' }}
                    </button>
                    <button type="button" class="btn-primary !min-h-8 !px-3 text-xs" data-testid="dsa-detail-submit-button"
                      [disabled]="busy() !== null" (click)="submit()">
                      <svg class="h-3.5 w-3.5" lucideIcon="send" aria-hidden="true"></svg>
                      {{ busy() === 'submit' ? 'Judging…' : 'Submit' }}
                    </button>
                  </div>
                </div>
                <div class="min-h-0 flex-1">
                  <app-markdown-editor #editor [content]="initialCode" [language]="language()" [theme]="theme()" (contentChange)="onCodeChange($event)" />
                </div>
              </div>

              <div class="panel !p-0 flex max-h-[45%] min-h-0 flex-col">
                <div class="tab-bar px-2" role="tablist">
                  <button type="button" role="tab" class="tab-bar__btn" [class.active]="consoleTab() === 'cases'"
                    [attr.aria-selected]="consoleTab() === 'cases'" data-testid="dsa-detail-console-cases" (click)="consoleTab.set('cases')">
                    Test cases
                  </button>
                  <button type="button" role="tab" class="tab-bar__btn" [class.active]="consoleTab() === 'result'"
                    [attr.aria-selected]="consoleTab() === 'result'" data-testid="dsa-detail-console-result" (click)="consoleTab.set('result')">
                    Result
                  </button>
                </div>
                <div class="min-h-0 flex-1 space-y-3 overflow-auto p-3">
                  @if (actionError()) {
                    <p class="text-sm" role="alert" style="color: var(--danger)" data-testid="dsa-detail-action-error">{{ actionError() }}</p>
                  }
                  @if (consoleTab() === 'cases') {
                    <app-dsa-test-cases [fields]="fields()" [cases]="cases()" [max]="maxCases" [(selected)]="selectedCase"
                      (casesChange)="setCases($event)" (resetToExamples)="resetCases()" />
                  } @else if (lastAction() === 'run' && runResult()) {
                    <app-dsa-run-results [result]="runResult()!" [signature]="p.signature" />
                  } @else if (lastAction() === 'submit' && submission()) {
                    <app-dsa-submission-result [submission]="submission()!" [signature]="p.signature" [canUseAsTestCase]="true"
                      (useAsTestCase)="useAsTestCase($event)" />
                  } @else if (busy()) {
                    <p class="text-xs" style="color: var(--text-muted)">Queued…</p>
                  } @else if (!actionError()) {
                    <p class="text-xs" style="color: var(--text-faint)">
                      Run executes your test cases and checks the ones that match an example. Submit checks every test.
                    </p>
                  }
                </div>
              </div>
            } @else {
              <div class="panel">
                <app-dsa-state title="Coming soon" message="You can solve this problem once its tests are added." />
              </div>
            }
          </section>
        </div>
      }
    </div>
  `,
})
export class ProblemDetailPageComponent implements OnInit, OnDestroy {
  readonly dsa = inject(DsaService);
  private readonly drafts = inject(DsaDraftStore);
  private readonly route = inject(ActivatedRoute);
  private readonly confirm = inject(ConfirmService);
  private readonly themeService = inject(ThemeService);

  @ViewChild('editor') editor?: MarkdownEditorComponent;
  @ViewChild('splitGrid') splitGrid?: ElementRef<HTMLElement>;

  readonly labels = LANGUAGE_LABELS;
  readonly maxCases = MAX_RUN_CASES;
  readonly json = formatJson;
  readonly theme = this.themeService.resolved;

  readonly problem = signal<ProblemDetail | null>(null);
  readonly loading = signal(true);
  readonly loadError = signal(false);
  readonly notFound = signal(false);
  readonly tab = signal<Tab>('description');
  readonly language = signal<DsaLanguage>('python');
  readonly busy = signal<Action | null>(null);
  readonly lastAction = signal<Action | null>(null);
  readonly runResult = signal<RunResult | null>(null);
  readonly submission = signal<SubmissionDetail | null>(null);
  readonly actionError = signal<string | null>(null);
  readonly consoleTab = signal<ConsoleTab>('cases');
  /** Run test cases: per case, one JSON text per input field. */
  readonly cases = signal<string[][]>([]);
  readonly selectedCase = signal(0);
  readonly fields = computed(() => inputFields(this.problem()?.signature ?? null));
  readonly historyVersion = signal(0);
  readonly splitMin = 0.25;
  readonly splitMax = 0.75;
  /** Description column's share of the desktop split. */
  readonly splitRatio = signal(this.clampSplit(this.drafts.splitRatio()));
  readonly splitColumns = computed(() => `minmax(0,${this.splitRatio()}fr) auto minmax(0,${1 - this.splitRatio()}fr)`);

  /** Content the editor is created with; later changes go through the editor API. */
  initialCode = '';
  private code = '';
  private saveTimer: ReturnType<typeof setTimeout> | null = null;
  private job?: Subscription;

  constructor() {
    effect(() => this.editor?.setTheme(this.theme()));
  }

  setSplit(ratio: number): void {
    this.splitRatio.set(ratio);
    this.drafts.rememberSplitRatio(ratio);
  }

  /** Extent of the whole two-column grid, read while dragging the divider. */
  readonly splitBounds = (): SplitBounds | null => {
    const rect = this.splitGrid?.nativeElement.getBoundingClientRect();
    return rect ? { start: rect.left, end: rect.right } : null;
  };

  private clampSplit(ratio: number | null): number {
    return Math.min(this.splitMax, Math.max(this.splitMin, ratio ?? 0.5));
  }

  private get slug(): string {
    return this.route.snapshot.paramMap.get('slug') ?? '';
  }

  ngOnInit(): void {
    this.dsa.me().subscribe({ error: () => undefined });
    this.load();
  }

  ngOnDestroy(): void {
    if (this.saveTimer) this.flushDraft();
    this.job?.unsubscribe();
  }

  load(): void {
    this.loading.set(true);
    this.loadError.set(false);
    this.notFound.set(false);
    this.dsa.problem(this.slug).subscribe({
      next: (p) => {
        const remembered = this.drafts.lastLanguage();
        const language = remembered && p.languages.includes(remembered) ? remembered : (p.languages[0] ?? 'python');
        this.language.set(language);
        this.code = this.initialCodeFor(p, language);
        this.initialCode = this.code;
        this.cases.set(this.initialCases(p));
        this.problem.set(p);
        this.loading.set(false);
      },
      error: (err: { status?: number }) => {
        if (err.status === 404) this.notFound.set(true);
        else this.loadError.set(true);
        this.loading.set(false);
      },
    });
  }

  private initialCodeFor(p: ProblemDetail, language: DsaLanguage): string {
    return this.drafts.load(p.slug, language) ?? p.starter_code[language] ?? '';
  }

  changeLanguage(language: DsaLanguage): void {
    const p = this.problem();
    if (!p) return;
    this.flushDraft();
    this.language.set(language);
    this.drafts.rememberLanguage(language);
    this.setEditorCode(this.initialCodeFor(p, language));
    this.editor?.setLanguage(language);
  }

  onCodeChange(code: string): void {
    this.code = code;
    if (this.saveTimer) clearTimeout(this.saveTimer);
    this.saveTimer = setTimeout(() => this.flushDraft(), DRAFT_SAVE_DELAY_MS);
  }

  private flushDraft(): void {
    if (this.saveTimer) clearTimeout(this.saveTimer);
    this.saveTimer = null;
    const p = this.problem();
    if (p) this.drafts.save(p.slug, this.language(), this.code);
  }

  private setEditorCode(code: string): void {
    this.code = code;
    this.editor?.setContent(code);
  }

  async reset(): Promise<void> {
    const p = this.problem();
    if (!p) return;
    const ok = await this.confirm.confirm('Replace your code with the starter code for this language?', 'Reset code');
    if (!ok) return;
    this.drafts.clear(p.slug, this.language());
    this.setEditorCode(p.starter_code[this.language()] ?? '');
  }

  loadIntoEditor(event: { code: string; language: DsaLanguage }): void {
    if (event.language !== this.language()) {
      this.flushDraft();
      this.language.set(event.language);
      this.editor?.setLanguage(event.language);
    }
    this.setEditorCode(event.code);
    this.flushDraft();
    this.tab.set('description');
  }

  /** The cases saved for this problem if they still fit its signature, else its examples. */
  private initialCases(p: ProblemDetail): string[][] {
    const width = inputFields(p.signature).length;
    const saved = this.drafts.loadCases(p.slug);
    const fits = saved !== null && saved.length > 0 && saved.length <= MAX_RUN_CASES && saved.every((c) => c.length === width);
    return fits ? saved : this.exampleCases(p);
  }

  private exampleCases(p: ProblemDetail): string[][] {
    const cases = p.samples
      .slice(0, MAX_RUN_CASES)
      .map((s) => this.caseTexts(p, s.input))
      .filter((texts): texts is string[] => texts !== null);
    return cases.length > 0 ? cases : [inputFields(p.signature).map(() => '')];
  }

  private caseTexts(p: ProblemDetail, input: JsonValue): string[] | null {
    return splitInput(p.signature, input)?.map((value) => formatJson(value)) ?? null;
  }

  setCases(cases: string[][]): void {
    this.cases.set(cases);
    const p = this.problem();
    if (p) this.drafts.saveCases(p.slug, cases);
  }

  resetCases(): void {
    const p = this.problem();
    if (!p) return;
    this.drafts.clearCases(p.slug);
    this.cases.set(this.exampleCases(p));
    this.selectedCase.set(0);
  }

  /** Adds a (failed) test's input to the Run test cases and shows it. */
  useAsTestCase(input: JsonValue): void {
    const p = this.problem();
    if (!p) return;
    const texts = this.caseTexts(p, input);
    this.consoleTab.set('cases');
    if (texts === null) {
      this.actionError.set("This test doesn't match the problem's current inputs.");
    } else if (formatJson(input).length > MAX_RUN_INPUT_BYTES) {
      this.actionError.set('This test is too large to run as a test case.');
    } else if (this.cases().length >= MAX_RUN_CASES) {
      this.actionError.set(`You already have ${MAX_RUN_CASES} test cases. Delete one, then try again.`);
    } else {
      this.actionError.set(null);
      this.setCases([...this.cases(), texts]);
      this.selectedCase.set(this.cases().length - 1);
    }
  }

  /** Every case as a Run input, or null (with the first bad field shown) if any field isn't JSON. */
  private parsedCases(p: ProblemDetail): JsonValue[] | null {
    const fields = this.fields();
    const inputs: JsonValue[] = [];
    for (const [i, texts] of this.cases().entries()) {
      const values: JsonValue[] = [];
      for (const [f, text] of texts.entries()) {
        const value = parseJson(text);
        if (value === undefined) {
          this.actionError.set(`Case ${i + 1}: ${fields[f]?.name ?? 'input'} is not valid JSON.`);
          this.selectedCase.set(i);
          this.consoleTab.set('cases');
          return null;
        }
        values.push(value);
      }
      inputs.push(joinInput(p.signature, values));
    }
    return inputs;
  }

  run(): void {
    const p = this.problem();
    if (!p) return;
    const inputs = this.parsedCases(p);
    if (inputs === null) return;
    this.start('run');
    this.runResult.set(null);
    this.job = this.dsa.run(p.slug, { language: this.language(), code: this.code, inputs }).subscribe({
      next: (r) => this.runResult.set(r),
      error: (err: unknown) => this.fail(err),
      complete: () => this.busy.set(null),
    });
  }

  submit(): void {
    const p = this.problem();
    if (!p) return;
    this.start('submit');
    this.submission.set(null);
    this.job = this.dsa.submit(p.slug, { language: this.language(), code: this.code }).subscribe({
      next: (s) => {
        this.submission.set(s);
        if (isTerminal(s.status)) this.afterSubmit(p, s);
      },
      error: (err: unknown) => this.fail(err),
      complete: () => this.busy.set(null),
    });
  }

  private start(action: Action): void {
    this.flushDraft();
    this.job?.unsubscribe();
    this.actionError.set(null);
    this.busy.set(action);
    this.lastAction.set(action);
    this.consoleTab.set('result');
  }

  private fail(err: unknown): void {
    this.actionError.set(actionErrorMessage(err));
    this.busy.set(null);
  }

  private afterSubmit(p: ProblemDetail, s: SubmissionDetail): void {
    this.historyVersion.update((v) => v + 1);
    if (s.verdict === 'Internal Error' || p.progress === 'solved') return;
    this.problem.set({ ...p, progress: s.verdict === 'Accepted' ? 'solved' : 'attempted' });
  }
}
