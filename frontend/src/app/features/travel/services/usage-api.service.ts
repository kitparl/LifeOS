import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { MapsSettings, PricingRow, UsageSummary } from '../models/travel.models';

/** Maps usage dashboard, cost protection settings and the editable rates (spec §27–§29, §31a). */
@Injectable({ providedIn: 'root' })
export class UsageApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/travel/usage`;

  summary(month?: string): Observable<UsageSummary> {
    const params = month ? new HttpParams().set('month', month) : undefined;
    return this.http.get<UsageSummary>(this.base, { params });
  }

  settings(): Observable<MapsSettings> {
    return this.http.get<MapsSettings>(`${this.base}/settings`);
  }

  saveSettings(body: Partial<Omit<MapsSettings, 'pricing_last_reviewed_at'>>): Observable<MapsSettings> {
    return this.http.put<MapsSettings>(`${this.base}/settings`, body);
  }

  pricing(): Observable<PricingRow[]> {
    return this.http.get<PricingRow[]>(`${this.base}/pricing`);
  }

  savePricing(rows: Omit<PricingRow, 'label'>[]): Observable<PricingRow[]> {
    return this.http.put<PricingRow[]>(`${this.base}/pricing`, { rows });
  }
}
