import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { EMPTY, Observable, expand, shareReplay, switchMap, tap, throwError, timer } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  AdminProblemDetail,
  AdminTestCase,
  CaseWrite,
  DsaMe,
  DsaNote,
  DsaNoteScope,
  JobAccepted,
  JobStatus,
  PatternDetail,
  PatternSummary,
  ProblemDetail,
  ProblemUpdate,
  RunRequest,
  RunResult,
  SubmissionDetail,
  SubmissionPage,
  SubmitRequest,
  isTerminal,
} from '../models/dsa.models';

/** Poll delays (ms) after a job is accepted; the last value repeats. */
export const POLL_DELAYS_MS = [1000, 1500, 2000, 3000];
export const POLL_TIMEOUT_MS = 120_000;

export class DsaPollTimeoutError extends Error {
  constructor() {
    super('The judge is taking too long. Check back in a moment.');
  }
}

@Injectable({ providedIn: 'root' })
export class DsaService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/dsa`;
  private me$?: Observable<DsaMe>;

  /** Whether the current user may edit the catalog (loaded once from /dsa/me). */
  readonly canEdit = signal(false);

  /** Clock seam for tests. */
  now: () => number = () => Date.now();

  me(): Observable<DsaMe> {
    this.me$ ??= this.http.get<DsaMe>(`${this.api}/me`).pipe(
      tap((me) => this.canEdit.set(me.can_edit)),
      shareReplay({ bufferSize: 1, refCount: false }),
    );
    return this.me$;
  }

  patterns(): Observable<PatternSummary[]> {
    return this.http.get<PatternSummary[]>(`${this.api}/patterns`);
  }

  pattern(slug: string): Observable<PatternDetail> {
    return this.http.get<PatternDetail>(`${this.api}/patterns/${encodeURIComponent(slug)}`);
  }

  note(scope: DsaNoteScope, slug: string): Observable<DsaNote> {
    return this.http.get<DsaNote>(`${this.api}/${scope}/${encodeURIComponent(slug)}/note`);
  }

  /** Blank content deletes the note. */
  saveNote(scope: DsaNoteScope, slug: string, content: string): Observable<DsaNote> {
    return this.http.put<DsaNote>(`${this.api}/${scope}/${encodeURIComponent(slug)}/note`, { content });
  }

  problem(slug: string): Observable<ProblemDetail> {
    return this.http.get<ProblemDetail>(`${this.api}/problems/${encodeURIComponent(slug)}`);
  }

  /** Starts a Run and emits every poll result until the run finishes. */
  run(slug: string, body: RunRequest): Observable<RunResult> {
    return this.http
      .post<JobAccepted>(`${this.api}/problems/${encodeURIComponent(slug)}/run`, body)
      .pipe(switchMap((job) => this.pollUntilDone(() => this.http.get<RunResult>(`${this.api}/runs/${job.id}`))));
  }

  /** Submits and emits every poll result until judging finishes. */
  submit(slug: string, body: SubmitRequest): Observable<SubmissionDetail> {
    return this.http
      .post<JobAccepted>(`${this.api}/problems/${encodeURIComponent(slug)}/submissions`, body)
      .pipe(switchMap((job) => this.pollUntilDone(() => this.submission(job.id))));
  }

  submission(id: string): Observable<SubmissionDetail> {
    return this.http.get<SubmissionDetail>(`${this.api}/submissions/${id}`);
  }

  history(slug: string, limit: number, offset: number): Observable<SubmissionPage> {
    const params = new HttpParams().set('limit', limit).set('offset', offset);
    return this.http.get<SubmissionPage>(`${this.api}/problems/${encodeURIComponent(slug)}/submissions`, { params });
  }

  adminProblem(slug: string): Observable<AdminProblemDetail> {
    return this.http.get<AdminProblemDetail>(`${this.api}/admin/problems/${encodeURIComponent(slug)}`);
  }

  adminUpdateProblem(slug: string, body: ProblemUpdate): Observable<AdminProblemDetail> {
    return this.http.put<AdminProblemDetail>(`${this.api}/admin/problems/${encodeURIComponent(slug)}`, body);
  }

  adminAddTest(slug: string, body: CaseWrite): Observable<AdminTestCase> {
    return this.http.post<AdminTestCase>(`${this.api}/admin/problems/${encodeURIComponent(slug)}/tests`, body);
  }

  adminUpdateTest(id: string, body: CaseWrite): Observable<AdminTestCase> {
    return this.http.put<AdminTestCase>(`${this.api}/admin/tests/${id}`, body);
  }

  adminDeleteTest(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/admin/tests/${id}`);
  }

  private pollUntilDone<T extends { status: JobStatus }>(fetch: () => Observable<T>): Observable<T> {
    const started = this.now();
    let attempt = 0;
    return fetch().pipe(
      expand((result) => {
        if (isTerminal(result.status)) return EMPTY;
        if (this.now() - started >= POLL_TIMEOUT_MS) return throwError(() => new DsaPollTimeoutError());
        const delay = POLL_DELAYS_MS[Math.min(attempt++, POLL_DELAYS_MS.length - 1)];
        return timer(delay).pipe(switchMap(() => fetch()));
      }),
    );
  }
}
