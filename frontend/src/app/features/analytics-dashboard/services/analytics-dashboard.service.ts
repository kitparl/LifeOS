import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  AiInsightsResponse,
  AnalyticsOverview,
  GoalAnalytics,
  HabitAnalytics,
  JournalAnalytics,
  ProductivityAnalytics,
  WidgetDescriptor,
} from '../models/analytics-dashboard.models';

@Injectable({ providedIn: 'root' })
export class AnalyticsDashboardService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/analytics/dashboard`;

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  overview(rangeDays = 30): Observable<AnalyticsOverview> {
    return this.get<AnalyticsOverview>('', rangeDays, 'Failed to load overview');
  }

  summary(rangeDays = 30): Observable<AnalyticsOverview> {
    return this.get<AnalyticsOverview>('/summary', rangeDays, 'Failed to load summary');
  }

  productivity(rangeDays = 30): Observable<ProductivityAnalytics> {
    return this.get<ProductivityAnalytics>('/productivity', rangeDays, 'Failed to load productivity');
  }

  goals(rangeDays = 90): Observable<GoalAnalytics> {
    return this.get<GoalAnalytics>('/goals', rangeDays, 'Failed to load goals');
  }

  habits(rangeDays = 90): Observable<HabitAnalytics> {
    return this.get<HabitAnalytics>('/habits', rangeDays, 'Failed to load habits');
  }

  journal(rangeDays = 90): Observable<JournalAnalytics> {
    return this.get<JournalAnalytics>('/journal', rangeDays, 'Failed to load journal');
  }

  ai(): Observable<AiInsightsResponse> {
    this.loading.set(true);
    this.error.set(null);
    return this.http.get<AiInsightsResponse>(`${this.api}/ai`).pipe(
      tap({
        next: () => this.loading.set(false),
        error: () => {
          this.error.set('Failed to load AI insights');
          this.loading.set(false);
        },
      }),
    );
  }

  widgets(): Observable<WidgetDescriptor[]> {
    return this.http.get<WidgetDescriptor[]>(`${this.api}/widgets`);
  }

  private get<T>(path: string, rangeDays: number, errMsg: string): Observable<T> {
    this.loading.set(true);
    this.error.set(null);
    const params = new HttpParams().set('range_days', String(rangeDays));
    return this.http.get<T>(`${this.api}${path}`, { params }).pipe(
      tap({
        next: () => this.loading.set(false),
        error: () => {
          this.error.set(errMsg);
          this.loading.set(false);
        },
      }),
    );
  }
}
