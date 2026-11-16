import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { ActivityService } from './activity.service';

describe('ActivityService', () => {
  let service: ActivityService;
  let http: HttpTestingController;
  const imports = `${environment.apiUrl}/integrations/garmin`;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(ActivityService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('uploads files and the range as multipart form data', () => {
    const a = new File(['a'], 'a.fit');
    const b = new File(['b'], 'export.zip');

    service.startImport([a, b], 'all').subscribe((job) => expect(job.id).toBe('j1'));

    const req = http.expectOne(`${imports}/imports`);
    expect(req.request.method).toBe('POST');
    const form = req.request.body as FormData;
    expect(form.getAll('files').map((f) => (f as File).name)).toEqual(['a.fit', 'export.zip']);
    expect(form.get('range')).toBe('all');
    req.flush({ id: 'j1', status: 'queued' });
  });

  it('reads the total count of the sync log from the header', () => {
    service.listImports({ limit: 25, offset: 50 }).subscribe((page) => {
      expect(page.total).toBe(60);
      expect(page.items.length).toBe(1);
    });

    const req = http.expectOne((r) => r.url === `${imports}/imports`);
    expect(req.request.params.get('limit')).toBe('25');
    expect(req.request.params.get('offset')).toBe('50');
    req.flush([{ id: 'j1' }], { headers: { 'X-Total-Count': '60' } });
  });

  it('polls one import, reads the data summary and deletes imported data', () => {
    service.getImport('j1').subscribe();
    http.expectOne(`${imports}/imports/j1`).flush({ id: 'j1' });

    service.getImportedSummary().subscribe((s) => expect(s.activities).toBe(2));
    http
      .expectOne(`${imports}/data/summary`)
      .flush({ activities: 2, runs_created: 1, runs_merged_into_manual: 1, health_days: 0 });

    service.deleteImportedData().subscribe((r) => expect(r.runs_restored).toBe(1));
    const del = http.expectOne((r) => r.url === `${imports}/data`);
    expect(del.request.method).toBe('DELETE');
    expect(del.request.params.get('include_health')).toBe('false');
    del.flush({ activities_deleted: 2, runs_deleted: 1, runs_restored: 1, races_detached: 0, files_deleted: 2, health_days_deleted: 0 });

    service.deleteImportedData(true).subscribe();
    const withHealth = http.expectOne((r) => r.url === `${imports}/data`);
    expect(withHealth.request.params.get('include_health')).toBe('true');
    withHealth.flush({ activities_deleted: 0, runs_deleted: 0, runs_restored: 0, races_detached: 0, files_deleted: 0, health_days_deleted: 3 });
  });

  it('loads an activity and its series', () => {
    service.getActivity('a1').subscribe((a) => expect(a.id).toBe('a1'));
    http.expectOne(`${environment.apiUrl}/activities/a1`).flush({ id: 'a1' });
    service.getActivitySeries('a1').subscribe((s) => expect(s.sample_count).toBe(0));
    http.expectOne(`${environment.apiUrl}/activities/a1/series`).flush({ sample_count: 0 });
  });
});
