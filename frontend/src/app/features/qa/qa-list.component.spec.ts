import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, ParamMap, convertToParamMap } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { groupEntriesByMonth } from './qa-expandable-entry.component';
import { QAListComponent } from './qa-list.component';

describe('QAListComponent', () => {
  let fixture: ComponentFixture<QAListComponent>;
  let http: HttpTestingController;
  // Fresh per test: a shared subject leaks `view` between tests under random spec order.
  let queryParams$: BehaviorSubject<ParamMap>;

  beforeEach(async () => {
    queryParams$ = new BehaviorSubject(convertToParamMap({}));
    await TestBed.configureTestingModule({
      imports: [QAListComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useValue: {
            queryParamMap: queryParams$.asObservable(),
            snapshot: { queryParamMap: convertToParamMap({}) },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(QAListComponent);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function flushTypesAndList(total = '0'): void {
    http.expectOne(`${environment.apiUrl}/qa/types`).flush(['Personal']);
    const listReq = http.expectOne((r) => r.url === `${environment.apiUrl}/qa/entries`);
    listReq.flush([], { headers: { 'X-Total-Count': total } });
  }

  it('should load entries on init', () => {
    fixture.detectChanges();
    flushTypesAndList();
    expect(fixture.componentInstance.entries).toEqual([]);
  });

  it('should reset page when filters are applied', () => {
    fixture.detectChanges();
    flushTypesAndList('25');
    fixture.componentInstance.currentPage = 2;
    fixture.componentInstance.applyFilters();
    expect(fixture.componentInstance.currentPage).toBe(1);
    http.expectOne((r) => r.url === `${environment.apiUrl}/qa/entries`);
  });

  it('should lazy-load answer on expand', () => {
    fixture.detectChanges();
    flushTypesAndList();
    fixture.componentInstance.entries = [
      {
        id: 'e1',
        question: 'Why?',
        current_answer: null,
        type: 'Personal',
        tags: [],
        is_deep_personal: true,
        created_at: '2026-08-17T00:00:00Z',
        updated_at: '2026-08-18T00:00:00Z',
      },
    ];
    fixture.componentInstance.toggleExpand('e1');
    const detailReq = http.expectOne(`${environment.apiUrl}/qa/entries/e1`);
    detailReq.flush({
      id: 'e1',
      question: 'Why?',
      current_answer: 'Because.',
      type: 'Personal',
      tags: [],
      is_deep_personal: true,
      linked_journal_id: null,
      ai_summary: null,
      created_at: '2026-08-17T00:00:00Z',
      updated_at: '2026-08-18T00:00:00Z',
      versions: [],
    });
    expect(fixture.componentInstance.getAnswer(fixture.componentInstance.entries[0])).toBe('Because.');
  });

  it('should soft-delete after confirmation', async () => {
    const confirm = TestBed.inject(ConfirmService);
    spyOn(confirm, 'confirm').and.resolveTo(true);
    fixture.detectChanges();
    flushTypesAndList();
    fixture.componentInstance.entries = [
      {
        id: 'e1',
        question: 'Why?',
        current_answer: null,
        type: 'Personal',
        tags: [],
        is_deep_personal: true,
        created_at: '2026-08-17T00:00:00Z',
        updated_at: '2026-08-18T00:00:00Z',
      },
    ];
    await fixture.componentInstance.removeEntry('e1');
    expect(confirm.confirm).toHaveBeenCalledWith(
      jasmine.stringMatching(/Deleted tab/),
      'Delete Q&A',
    );
    const delReq = http.expectOne(`${environment.apiUrl}/qa/entries/e1`);
    expect(delReq.request.method).toBe('DELETE');
    delReq.flush(null);
    http.expectOne((r) => r.url === `${environment.apiUrl}/qa/entries`).flush([], {
      headers: { 'X-Total-Count': '0' },
    });
  });

  it('should list deleted entries and restore them', () => {
    fixture.detectChanges();
    flushTypesAndList();
    queryParams$.next(convertToParamMap({ view: 'deleted' }));
    const listReq = http.expectOne((r) => r.url === `${environment.apiUrl}/qa/entries`);
    expect(listReq.request.params.get('deleted')).toBe('true');
    listReq.flush(
      [
        {
          id: 'e1',
          question: 'Should I save money?',
          current_answer: 'Yes.',
          type: 'Personal',
          tags: [],
          is_deep_personal: false,
          created_at: '2026-08-17T00:00:00Z',
          updated_at: '2026-08-18T00:00:00Z',
          deleted_at: '2026-09-19T00:00:00Z',
        },
      ],
      { headers: { 'X-Total-Count': '1' } },
    );
    expect(fixture.componentInstance.view).toBe('deleted');
    expect(fixture.componentInstance.entries.length).toBe(1);

    fixture.componentInstance.restoreEntry('e1');
    const restoreReq = http.expectOne(`${environment.apiUrl}/qa/entries/e1/restore`);
    expect(restoreReq.request.method).toBe('POST');
    restoreReq.flush({
      id: 'e1',
      question: 'Should I save money?',
      current_answer: 'Yes.',
      type: 'Personal',
      tags: [],
      is_deep_personal: false,
      linked_journal_id: null,
      ai_summary: null,
      created_at: '2026-08-17T00:00:00Z',
      updated_at: '2026-08-18T00:00:00Z',
      versions: [],
    });
    http.expectOne((r) => r.url === `${environment.apiUrl}/qa/entries`).flush([], {
      headers: { 'X-Total-Count': '0' },
    });
  });
});

describe('groupEntriesByMonth', () => {
  it('should group entries by year-month', () => {
    const groups = groupEntriesByMonth([
      {
        id: '1',
        question: 'A?',
        current_answer: null,
        type: null,
        tags: [],
        is_deep_personal: false,
        created_at: '2026-08-17T00:00:00Z',
        updated_at: '2026-08-17T00:00:00Z',
      },
      {
        id: '2',
        question: 'B?',
        current_answer: null,
        type: null,
        tags: [],
        is_deep_personal: false,
        created_at: '2026-07-10T00:00:00Z',
        updated_at: '2026-07-10T00:00:00Z',
      },
    ]);
    expect(groups.length).toBe(2);
    expect(groups[0].entries.length).toBe(1);
    expect(groups[0].label).toContain('2026');
  });
});
