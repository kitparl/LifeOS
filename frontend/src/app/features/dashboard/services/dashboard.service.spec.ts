import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { DashboardService } from './dashboard.service';

describe('DashboardService', () => {
  let service: DashboardService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(DashboardService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('should load dashboard summary', () => {
    const mock = {
      sync_status: 'synced',
      pending_sync_count: 0,
      tasks_today: [],
      habits_today: [],
      goals_progress: [],
      running_progress: null,
      calendar_preview: [],
      notifications: [],
      recent_activity: [],
      quick_actions: [],
    };

    service.getSummary().subscribe((data) => {
      expect(data.sync_status).toBe('synced');
    });

    const req = http.expectOne(`${environment.apiUrl}/dashboard/summary`);
    expect(req.request.method).toBe('GET');
    req.flush(mock);

    expect(service.summary()?.sync_status).toBe('synced');
    expect(service.loading()).toBeFalse();
  });
});
