import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
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

@Injectable({ providedIn: 'root' })
export class AutomationsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/automations`;

  list(): Observable<AutomationRule[]> {
    return this.http.get<AutomationRule[]>(`${this.api}/rules`);
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
