import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { AiChatResponse, AiIndexResponse, AiStatus } from '../models/ai.models';

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
}
