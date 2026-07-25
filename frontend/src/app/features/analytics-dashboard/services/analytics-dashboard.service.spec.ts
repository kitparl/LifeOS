import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { AnalyticsDashboardService } from './analytics-dashboard.service';

describe('AnalyticsDashboardService', () => {
  let service: AnalyticsDashboardService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AnalyticsDashboardService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('should load overview', () => {
    const mock = {
      life_score: 50,
      todays_tasks: 0,
      completed_tasks: 0,
      goal_progress: 50,
      habit_score: 50,
      focus_time_hours: 0,
      focus_time_label: 'planned',
      journal_streak: 0,
      mood_score: null,
      upcoming_events: [],
      recent_activity: [],
      kpis: [],
      range_days: 30,
    };

    service.overview().subscribe((data) => {
      expect(data.life_score).toBe(50);
    });

    const req = http.expectOne(`${environment.apiUrl}/analytics/dashboard?range_days=30`);
    expect(req.request.method).toBe('GET');
    req.flush(mock);
    expect(service.loading()).toBeFalse();
  });

  it('should load AI insights', () => {
    const mock = {
      daily: { period: 'daily', status: 'coming_soon', title: 'Daily', items: [], message: 'soon' },
      weekly: { period: 'weekly', status: 'coming_soon', title: 'Weekly', items: [], message: 'soon' },
      monthly: { period: 'monthly', status: 'coming_soon', title: 'Monthly', items: [], message: 'soon' },
      predictions: {
        period: 'predictions',
        status: 'coming_soon',
        title: 'Predictions',
        items: [],
        message: 'soon',
      },
    };

    service.ai().subscribe((data) => {
      expect(data.daily.status).toBe('coming_soon');
    });

    const req = http.expectOne(`${environment.apiUrl}/analytics/dashboard/ai`);
    expect(req.request.method).toBe('GET');
    req.flush(mock);
  });
});
