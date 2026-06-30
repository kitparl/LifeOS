import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface CoachChatResponse {
  coach_type: string;
  reply: string;
  context_summary: string;
}

@Injectable({ providedIn: 'root' })
export class CoachesService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/coaches`;

  types(): Observable<{ types: string[] }> {
    return this.http.get<{ types: string[] }>(`${this.api}/types`);
  }

  chat(coachType: string, message: string): Observable<CoachChatResponse> {
    return this.http.post<CoachChatResponse>(`${this.api}/${coachType}/chat`, { message });
  }
}
