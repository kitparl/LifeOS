import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { PeriodReport, ReviewResponse } from '../models/reports.models';

@Injectable({ providedIn: 'root' })
export class ReportsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/reports`;

  getReport(period: string): Observable<PeriodReport> {
    return this.http.get<PeriodReport>(`${this.api}/${period}`);
  }

  createReview(type: string): Observable<ReviewResponse> {
    return this.http.post<ReviewResponse>(`${this.api}/reviews/${type}`, {});
  }
}
