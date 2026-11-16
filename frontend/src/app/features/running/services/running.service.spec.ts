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

  it('should delete a run', () => {
    service.deleteRun('1').subscribe((res) => expect(res).toBeNull());
    const req = http.expectOne(`${environment.apiUrl}/running/runs/1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('lists candidates, attaches a run to a race and detaches it', () => {
    service.listRaceCandidates('r1').subscribe((runs) => expect(runs.length).toBe(1));
    http.expectOne(`${environment.apiUrl}/running/races/r1/candidates`).flush([{ id: 'run1' }]);

    service.attachRun('r1', 'run1').subscribe((race) => expect(race.run_id).toBe('run1'));
    const attach = http.expectOne(`${environment.apiUrl}/running/races/r1/attachment`);
    expect(attach.request.method).toBe('PUT');
    expect(attach.request.body).toEqual({ run_id: 'run1' });
    attach.flush({ id: 'r1', run_id: 'run1' });

    service.detachRun('r1').subscribe((race) => expect(race.run_id).toBeNull());
    const detach = http.expectOne(`${environment.apiUrl}/running/races/r1/attachment`);
    expect(detach.request.method).toBe('DELETE');
    detach.flush({ id: 'r1', run_id: null });
  });
});
