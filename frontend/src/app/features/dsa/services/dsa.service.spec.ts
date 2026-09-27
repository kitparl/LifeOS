import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { SubmissionDetail } from '../models/dsa.models';
import { DsaPollTimeoutError, DsaService, POLL_TIMEOUT_MS } from './dsa.service';

describe('DsaService', () => {
  let service: DsaService;
  let http: HttpTestingController;
  let clock = 0;
  const api = `${environment.apiUrl}/dsa`;

  const submission = (status: SubmissionDetail['status'], verdict: string | null = null): SubmissionDetail => ({
    id: 's1',
    language: 'python',
    status,
    verdict,
    passed: 0,
    total: 3,
    runtime_ms: null,
    memory_kb: null,
    created_at: '2026-09-26T10:00:00Z',
    problem_slug: 'two-sum',
    code: 'x',
    failed_case: null,
    message: null,
  });

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(DsaService);
    http = TestBed.inject(HttpTestingController);
    clock = 0;
    service.now = () => clock;
  });

  afterEach(() => http.verify());

  it('loads /me once and exposes canEdit', () => {
    service.me().subscribe();
    service.me().subscribe();
    http.expectOne(`${api}/me`).flush({ can_edit: true });
    expect(service.canEdit()).toBeTrue();
  });

  it('url-encodes slugs', () => {
    service.problem('a b').subscribe();
    const req = http.expectOne(`${api}/problems/a%20b`);
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('submits, then polls with back-off until the result is terminal', fakeAsync(() => {
    const seen: string[] = [];
    let completed = false;
    service.submit('two-sum', { language: 'python', code: 'x' }).subscribe({
      next: (s) => seen.push(s.status),
      complete: () => (completed = true),
    });
    const post = http.expectOne(`${api}/problems/two-sum/submissions`);
    expect(post.request.method).toBe('POST');
    expect(post.request.body).toEqual({ language: 'python', code: 'x' });
    post.flush({ id: 's1', status: 'pending' });

    http.expectOne(`${api}/submissions/s1`).flush(submission('pending'));
    tick(999);
    http.expectNone(`${api}/submissions/s1`);
    tick(1);
    http.expectOne(`${api}/submissions/s1`).flush(submission('running'));
    tick(1500);
    http.expectOne(`${api}/submissions/s1`).flush(submission('done', 'Accepted'));
    expect(seen).toEqual(['pending', 'running', 'done']);
    expect(completed).toBeTrue();
  }));

  it('run sends custom inputs and polls /runs', fakeAsync(() => {
    let verdict: string | null = null;
    service.run('two-sum', { language: 'cpp', code: 'x', custom_inputs: [[[1], 2]] }).subscribe((r) => (verdict = r.verdict));
    const post = http.expectOne(`${api}/problems/two-sum/run`);
    expect(post.request.body.custom_inputs).toEqual([[[1], 2]]);
    post.flush({ id: 'r1', status: 'pending' });
    http.expectOne(`${api}/runs/r1`).flush({ id: 'r1', status: 'done', verdict: 'Accepted', message: null, cases: [], stdout: '', stderr: '' });
    expect(verdict as string | null).toBe('Accepted');
  }));

  it('gives up after the poll timeout', fakeAsync(() => {
    let error: unknown;
    service.submit('two-sum', { language: 'python', code: 'x' }).subscribe({ error: (e) => (error = e) });
    http.expectOne(`${api}/problems/two-sum/submissions`).flush({ id: 's1', status: 'pending' });
    clock = POLL_TIMEOUT_MS;
    http.expectOne(`${api}/submissions/s1`).flush(submission('running'));
    expect(error).toBeInstanceOf(DsaPollTimeoutError);
  }));

  it('passes paging params for history', () => {
    service.history('two-sum', 10, 20).subscribe();
    const req = http.expectOne((r) => r.url === `${api}/problems/two-sum/submissions`);
    expect(req.request.params.get('limit')).toBe('10');
    expect(req.request.params.get('offset')).toBe('20');
    req.flush({ items: [], total: 0 });
  });
});
