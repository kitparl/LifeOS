import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { QAService } from './qa.service';

describe('QAService', () => {
  let service: QAService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(QAService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should list entries with pagination params and parse X-Total-Count', () => {
    service
      .list({ limit: 20, offset: 0, include_answer: false, sort_by: 'updated_at' })
      .subscribe((result) => {
        expect(result.items.length).toBe(1);
        expect(result.total).toBe(42);
      });

    const req = http.expectOne((r) => r.url === `${environment.apiUrl}/qa/entries`);
    expect(req.request.params.get('limit')).toBe('20');
    expect(req.request.params.get('offset')).toBe('0');
    expect(req.request.params.get('include_answer')).toBe('false');
    expect(req.request.params.get('sort_by')).toBe('updated_at');
    req.flush(
      [
        {
          id: '1',
          question: 'Q?',
          current_answer: null,
          type: 'Personal',
          tags: [],
          is_deep_personal: false,
          created_at: '2026-08-01T00:00:00Z',
          updated_at: '2026-08-02T00:00:00Z',
        },
      ],
      { headers: { 'X-Total-Count': '42' } },
    );
  });

  it('should pass deep_personal filter', () => {
    service.list({ deep_personal: true, sort_by: 'created_at' }).subscribe();
    const req = http.expectOne((r) => r.url === `${environment.apiUrl}/qa/entries`);
    expect(req.request.params.get('deep_personal')).toBe('true');
    expect(req.request.params.get('sort_by')).toBe('created_at');
    req.flush([], { headers: { 'X-Total-Count': '0' } });
  });
});
