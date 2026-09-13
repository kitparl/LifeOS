import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { AnalyticsCharts, AnalyticsSummary } from '../models/analytics.models';

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/analytics`;

  summary(): Observable<AnalyticsSummary> {
    return this.http.get<AnalyticsSummary>(`${this.api}/summary`);
  }

  charts(): Observable<AnalyticsCharts> {
    return this.http.get<AnalyticsCharts>(`${this.api}/charts`);
  }
}
