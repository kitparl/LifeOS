import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { HabitsService } from './habits.service';

describe('HabitsService', () => {
  let service: HabitsService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(HabitsService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should create a habit', () => {
    service.create({ name: 'Meditate', frequency: 'daily' }).subscribe((h) => {
      expect(h.name).toBe('Meditate');
    });
    const req = http.expectOne(`${environment.apiUrl}/habits`);
    expect(req.request.method).toBe('POST');
    req.flush({
      id: '1',
      name: 'Meditate',
      description: null,
      frequency: 'daily',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      completed_today: false,
      streak: 0,
      completion_rate: 0,
      stats: { streak: 0, completion_rate: 0, total_logs: 0, missed_periods: 0, recent_logs: [] },
      logs: [],
    });
  });
});
