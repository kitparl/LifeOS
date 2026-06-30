import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/analytics`;

  summary(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.api}/summary`);
  }

  charts(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.api}/charts`);
  }
}
