import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface PredictionItem {
  key: string;
  label: string;
  score: number;
  level: string;
  summary: string;
}

export interface PredictionsSummary {
  running_readiness: PredictionItem;
  burnout_risk: PredictionItem;
  overspending_risk: PredictionItem;
  learning_consistency: PredictionItem;
  goal_completion_probability: PredictionItem;
}

@Injectable({ providedIn: 'root' })
export class PredictionsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/predictions`;

  summary(): Observable<PredictionsSummary> {
    return this.http.get<PredictionsSummary>(`${this.api}/summary`);
  }
}
