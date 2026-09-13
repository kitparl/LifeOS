import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface AutomationRule {
  id: string;
  name: string;
  trigger_type: string;
  action_type: string;
  enabled: boolean;
  last_run_at: string | null;
}

export interface AutomationEvaluateResponse {
  evaluated: number;
  triggered: number;
  results: { rule_name: string; triggered: boolean; message: string | null }[];
}

export interface AutomationListResult {
  items: AutomationRule[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class AutomationsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/automations`;

  list(opts?: { limit?: number; offset?: number }): Observable<AutomationListResult> {
    let params = new HttpParams();
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<AutomationRule[]>(`${this.api}/rules`, { params, observe: 'response' }).pipe(
      map((response: HttpResponse<AutomationRule[]>) => ({
        items: response.body ?? [],
        total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
      })),
    );
  }

  create(data: {
    name: string;
    trigger_type: string;
    action_type: string;
    condition_json?: string;
    enabled?: boolean;
  }): Observable<AutomationRule> {
    return this.http.post<AutomationRule>(`${this.api}/rules`, data);
  }

  evaluate(): Observable<AutomationEvaluateResponse> {
    return this.http.post<AutomationEvaluateResponse>(`${this.api}/evaluate`, {});
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/rules/${id}`);
  }
}
