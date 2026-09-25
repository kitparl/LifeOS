import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  AiChatResponse,
  AiIndexResponse,
  AiSettings,
  AiStatus,
  AiUseCase,
  AiUseCaseHistoryItem,
  AiUseCaseModelUpdate,
} from '../models/ai.models';

@Injectable({ providedIn: 'root' })
export class AiService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/ai`;

  status(): Observable<AiStatus> {
    return this.http.get<AiStatus>(`${this.api}/status`);
  }

  index(): Observable<AiIndexResponse> {
    return this.http.post<AiIndexResponse>(`${this.api}/index`, {});
  }

  chat(message: string): Observable<AiChatResponse> {
    return this.http.post<AiChatResponse>(`${this.api}/chat`, { message });
  }

  listUseCases(): Observable<AiUseCase[]> {
    return this.http.get<AiUseCase[]>(`${this.api}/use-cases`);
  }

  setUseCaseModel(useCase: string, body: AiUseCaseModelUpdate): Observable<AiUseCase> {
    return this.http.put<AiUseCase>(`${this.api}/use-cases/${encodeURIComponent(useCase)}/model`, body);
  }

  useCaseHistory(useCase: string): Observable<AiUseCaseHistoryItem[]> {
    return this.http.get<AiUseCaseHistoryItem[]>(`${this.api}/use-cases/${encodeURIComponent(useCase)}/history`);
  }

  getSettings(): Observable<AiSettings> {
    return this.http.get<AiSettings>(`${this.api}/settings`);
  }

  saveSettings(body: AiSettings): Observable<AiSettings> {
    return this.http.put<AiSettings>(`${this.api}/settings`, body);
  }
}
