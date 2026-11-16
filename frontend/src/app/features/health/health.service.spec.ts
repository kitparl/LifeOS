import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../environments/environment';
import { HealthService } from './services/health.service';

describe('HealthService', () => {
  let service: HealthService;
  let http: HttpTestingController;
  const api = `${environment.apiUrl}/health`;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(HealthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('reads the catalogue, today, a trend and sleep', () => {
    service.getCatalogue().subscribe((c) => expect(c.length).toBe(1));
    http.expectOne(`${api}/metrics`).flush([{ key: 'resting_hr' }]);

    service.getToday().subscribe((t) => expect(t.is_today).toBeTrue());
    http.expectOne(`${api}/today`).flush({ day: '2026-05-20', is_today: true, metrics: [] });

    service.getMetricSeries('hrv_ms', '90d').subscribe();
    const trend = http.expectOne((r) => r.url === `${api}/metrics/hrv_ms`);
    expect(trend.request.params.get('range')).toBe('90d');
    trend.flush({ key: 'hrv_ms', points: [], rolling: [] });

    service.getSleep('7d').subscribe();
    const sleep = http.expectOne((r) => r.url === `${api}/sleep`);
    expect(sleep.request.params.get('range')).toBe('7d');
    sleep.flush({ nights: [] });
  });

  it('reads and saves one day with the values wrapped as the API expects', () => {
    service.getDay('2026-05-20').subscribe();
    http.expectOne(`${api}/days/2026-05-20`).flush({ day: '2026-05-20', values: {}, sources: {} });

    service.saveDay('2026-05-20', { resting_hr: 52 }).subscribe();
    const put = http.expectOne(`${api}/days/2026-05-20`);
    expect(put.request.method).toBe('PUT');
    expect(put.request.body).toEqual({ values: { resting_hr: 52 } });
    put.flush({ day: '2026-05-20', values: { resting_hr: 52 }, sources: { resting_hr: 'manual' } });
  });

  it('lists, adds and deletes measurements', () => {
    service.listMeasurements('weight', '2026-02-01', '2026-05-01').subscribe();
    const list = http.expectOne((r) => r.url === `${api}/measurements`);
    expect(list.request.params.get('kind')).toBe('weight');
    expect(list.request.params.get('start')).toBe('2026-02-01');
    list.flush([]);

    service.addMeasurement({ kind: 'weight', values: { weight_kg: 72.5 } }).subscribe();
    const post = http.expectOne(`${api}/measurements`);
    expect(post.request.method).toBe('POST');
    post.flush({ id: 'm1' });

    service.deleteMeasurement('m1').subscribe();
    const del = http.expectOne(`${api}/measurements/m1`);
    expect(del.request.method).toBe('DELETE');
    del.flush(null);
  });
});
