import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { RunningService } from './running.service';

describe('RunningService', () => {
  let service: RunningService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(RunningService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should create a run', () => {
    service
      .createRun({ run_date: '2026-06-30', distance_km: 5, duration_seconds: 1500 })
      .subscribe((r) => expect(r.distance_km).toBe(5));
    const req = http.expectOne(`${environment.apiUrl}/running/runs`);
    expect(req.request.method).toBe('POST');
    req.flush({
      id: '1',
      run_date: '2026-06-30',
      distance_km: 5,
      duration_seconds: 1500,
      pace_min_per_km: 5,
      weather: null,
      notes: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  });
});
