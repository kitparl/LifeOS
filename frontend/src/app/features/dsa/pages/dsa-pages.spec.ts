import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import {
  LucideChevronLeft,
  LucideCircle,
  LucideCircleCheck,
  LucideCircleDot,
  LucidePencil,
  LucidePlay,
  LucidePlus,
  LucideRotateCcw,
  LucideSend,
  LucideTrash2,
  provideLucideIcons,
} from '@lucide/angular';
import { BehaviorSubject } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { AdminProblemDetail, PatternDetail, PatternSummary, ProblemDetail } from '../models/dsa.models';
import { DsaDraftStore } from '../services/dsa-draft.store';
import { DsaPollTimeoutError } from '../services/dsa.service';
import { problemChanges, serverMessage } from './admin-problem-editor.page';
import { DsaOverviewPageComponent } from './dsa-overview.page';
import { PatternProblemsPageComponent } from './pattern-problems.page';
import { ProblemDetailPageComponent, actionErrorMessage } from './problem-detail.page';

const api = `${environment.apiUrl}/dsa`;
const icons = provideLucideIcons(
  LucideChevronLeft,
  LucideCircle,
  LucideCircleCheck,
  LucideCircleDot,
  LucidePencil,
  LucidePlay,
  LucidePlus,
  LucideRotateCcw,
  LucideSend,
  LucideTrash2,
);

const summary = (slug: string, week: number, number: number): PatternSummary => ({
  slug,
  number,
  name: slug,
  description: 'd',
  week,
  total: 4,
  solved: 1,
  attempted: 2,
});

const PROBLEM: ProblemDetail = {
  slug: 'two-sum',
  title: 'Two Sum',
  difficulty: 'easy',
  tags: ['blind75'],
  is_variant: false,
  status: 'published',
  pattern_slug: 'two-pointers',
  pattern_name: 'Two Pointers',
  statement: 'Find two numbers.',
  constraints: '- small',
  signature: { kind: 'function', name: 'twoSum' },
  time_limit_ms: 1000,
  memory_limit_mb: 256,
  samples: [{ input: [[2, 7], 9], expected: [0, 1], explanation: '2 + 7 = 9' }],
  starter_code: { python: 'class Solution: ...', cpp: '// cpp starter' },
  languages: ['python', 'cpp'],
  progress: 'not_started',
};

function setup(params: Record<string, string> = {}, query$ = new BehaviorSubject(convertToParamMap({}))) {
  TestBed.configureTestingModule({
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      provideRouter([]),
      icons,
      {
        provide: ActivatedRoute,
        useValue: {
          snapshot: { paramMap: convertToParamMap(params) },
          paramMap: new BehaviorSubject(convertToParamMap(params)),
          queryParamMap: query$,
        },
      },
    ],
  });
  return TestBed.inject(HttpTestingController);
}

describe('DsaOverviewPageComponent', () => {
  it('groups patterns by week in order', () => {
    const http = setup();
    const fixture = TestBed.createComponent(DsaOverviewPageComponent);
    fixture.detectChanges();
    http.expectOne(`${api}/patterns`).flush([summary('b', 2, 9), summary('a', 1, 1), summary('c', 1, 2)]);
    fixture.detectChanges();
    const headings = [...fixture.nativeElement.querySelectorAll('h2')].map((h: HTMLElement) => h.textContent?.trim());
    expect(headings).toEqual(['Week 1', 'Week 2']);
    expect(fixture.nativeElement.querySelector('[data-testid="dsa-overview-pattern-a"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[data-testid="dsa-overview-totals"]').textContent).toContain('3 solved');
    http.verify();
  });

  it('shows a retryable error', () => {
    const http = setup();
    const fixture = TestBed.createComponent(DsaOverviewPageComponent);
    fixture.detectChanges();
    http.expectOne(`${api}/patterns`).flush('boom', { status: 500, statusText: 'err' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain("couldn't load the patterns");
    (fixture.nativeElement.querySelector('[data-testid="dsa-state-retry-button"]') as HTMLButtonElement).click();
    http.expectOne(`${api}/patterns`).flush([]);
    expect(fixture.componentInstance.error()).toBeFalse();
    http.verify();
  });
});

describe('PatternProblemsPageComponent', () => {
  const detail: PatternDetail = {
    ...summary('two-pointers', 1, 1),
    problems: [
      { slug: 'easy-one', title: 'Easy One', difficulty: 'easy', tags: [], is_variant: false, status: 'published', progress: 'solved' },
      { slug: 'hard-draft', title: 'Hard Draft', difficulty: 'hard', tags: ['blind75'], is_variant: true, status: 'draft', progress: 'not_started' },
    ],
  };

  it('links only published problems and filters by query params', () => {
    const query$ = new BehaviorSubject(convertToParamMap({}));
    const http = setup({ slug: 'two-pointers' }, query$);
    const fixture: ComponentFixture<PatternProblemsPageComponent> = TestBed.createComponent(PatternProblemsPageComponent);
    fixture.detectChanges();
    http.expectOne(`${api}/patterns/two-pointers`).flush(detail);
    fixture.detectChanges();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[data-testid="dsa-problem-link-easy-one"]')).toBeTruthy();
    expect(el.querySelector('[data-testid="dsa-problem-link-hard-draft"]')).toBeNull();
    expect(el.querySelector('[data-testid="dsa-problem-row-hard-draft"]')?.textContent).toContain('Coming soon');

    query$.next(convertToParamMap({ difficulty: 'hard' }));
    fixture.detectChanges();
    expect(el.querySelector('[data-testid="dsa-problem-row-easy-one"]')).toBeNull();
    expect(el.querySelector('[data-testid="dsa-problem-row-hard-draft"]')).toBeTruthy();
    http.verify();
  });
});

describe('ProblemDetailPageComponent', () => {
  let fixture: ComponentFixture<ProblemDetailPageComponent>;
  let http: HttpTestingController;
  const el = () => fixture.nativeElement as HTMLElement;
  const click = (id: string) => (el().querySelector(`[data-testid="${id}"]`) as HTMLButtonElement).click();

  const create = () => {
    http = setup({ slug: 'two-sum' });
    const drafts = TestBed.inject(DsaDraftStore);
    const store = new Map<string, string>();
    drafts.storage = () =>
      ({ getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => void store.set(k, v), removeItem: () => undefined }) as unknown as Storage;
    fixture = TestBed.createComponent(ProblemDetailPageComponent);
    fixture.detectChanges();
    http.expectOne(`${api}/me`).flush({ can_edit: false });
    http.expectOne(`${api}/problems/two-sum`).flush(PROBLEM);
    fixture.detectChanges();
  };

  it('renders the statement, examples and starter code for the first language', () => {
    create();
    expect(el().textContent).toContain('Two Sum');
    expect(el().querySelector('[data-testid="dsa-detail-example-0"]')?.textContent).toContain('2 + 7 = 9');
    expect(fixture.componentInstance.initialCode).toBe('class Solution: ...');
    expect(el().querySelector('[data-testid="dsa-detail-edit-link"]')).toBeNull();
    http.verify();
  });

  it('runs with parsed custom inputs and shows results', fakeAsync(() => {
    create();
    fixture.componentInstance.customInputs.set(['[[1, 2], 3]']);
    fixture.detectChanges();
    click('dsa-detail-run-button');
    const post = http.expectOne(`${api}/problems/two-sum/run`);
    expect(post.request.body).toEqual({ language: 'python', code: 'class Solution: ...', custom_inputs: [[[1, 2], 3]] });
    post.flush({ id: 'r1', status: 'pending' });
    http.expectOne(`${api}/runs/r1`).flush({
      id: 'r1',
      status: 'done',
      verdict: 'Accepted',
      message: null,
      cases: [{ index: 0, input: [[2, 7], 9], expected: [0, 1], actual: [0, 1], passed: true, ms: 1.5, error: null, is_custom: false }],
      stdout: 'hello',
      stderr: '',
    });
    fixture.detectChanges();
    expect(el().querySelector('[data-testid="dsa-run-results"]')?.textContent).toContain('hello');
    expect(fixture.componentInstance.busy()).toBeNull();
    tick(1000);
    http.verify();
  }));

  it('rejects invalid custom JSON without calling the API', () => {
    create();
    fixture.componentInstance.customInputs.set(['[1,']);
    fixture.componentInstance.run();
    fixture.detectChanges();
    expect(el().querySelector('[data-testid="dsa-detail-action-error"]')?.textContent).toContain('not valid JSON');
    http.verify();
  });

  it('explains when the judge is not configured', fakeAsync(() => {
    create();
    click('dsa-detail-submit-button');
    http.expectOne(`${api}/problems/two-sum/submissions`).flush({ detail: 'The judge is not configured' }, { status: 503, statusText: 'x' });
    fixture.detectChanges();
    expect(el().querySelector('[data-testid="dsa-detail-action-error"]')?.textContent).toContain("isn't available");
    tick(1000);
    http.verify();
  }));

  it('marks the problem solved after an accepted submission', fakeAsync(() => {
    create();
    click('dsa-detail-submit-button');
    http.expectOne(`${api}/problems/two-sum/submissions`).flush({ id: 's1', status: 'pending' });
    http.expectOne(`${api}/submissions/s1`).flush({
      id: 's1', language: 'python', status: 'done', verdict: 'Accepted', passed: 5, total: 5, runtime_ms: 3, memory_kb: 2048,
      created_at: '2026-09-26T10:00:00Z', problem_slug: 'two-sum', code: 'x', failed_case: null, message: null,
    });
    fixture.detectChanges();
    expect(fixture.componentInstance.problem()?.progress).toBe('solved');
    expect(el().querySelector('[data-testid="dsa-submission-result"]')?.textContent).toContain('5/5');
    tick(1000);
    http.verify();
  }));
});

describe('DSA page helpers', () => {
  it('maps action errors to friendly text', () => {
    expect(actionErrorMessage(new DsaPollTimeoutError())).toContain('too long');
    expect(actionErrorMessage(new HttpErrorResponse({ status: 429, error: { detail: 'Too many runs' } }))).toBe('Too many runs');
    expect(actionErrorMessage(new HttpErrorResponse({ status: 500, error: { detail: 'trace' } }))).toContain('Something went wrong');
  });

  it('builds a minimal admin update and rejects bad signature JSON', () => {
    const p = { ...PROBLEM, compare_mode: 'exact', checker: null, edited_in_ui: false, tests: [] } as AdminProblemDetail;
    const form = {
      title: 'Two Sum', difficulty: 'easy' as const, status: 'published' as const, is_variant: false, tags: 'blind75',
      statement: 'New.', constraints: '- small', signature: JSON.stringify(p.signature), compare_mode: 'exact' as const,
      checker: '', time_limit_ms: 1000, memory_limit_mb: 256,
    };
    expect(problemChanges(p, form)).toEqual({ statement: 'New.' });
    expect(() => problemChanges(p, { ...form, signature: '{' })).toThrow();
    expect(serverMessage(new HttpErrorResponse({ status: 400, error: { detail: 'Bad test' } }))).toBe('Bad test');
  });
});
