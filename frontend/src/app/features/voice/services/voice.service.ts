import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface VoiceNote {
  id: string;
  title: string | null;
  transcript: string;
  note_type: string;
  command_result: string | null;
  created_at: string;
}

export interface VoiceCommandResponse {
  intent: string;
  route: string | null;
  message: string;
  transcript: string;
}

export interface VoiceListResult {
  items: VoiceNote[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class VoiceService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/voice`;

  list(opts?: { limit?: number; offset?: number }): Observable<VoiceListResult> {
    let params = new HttpParams();
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<VoiceNote[]>(`${this.api}/notes`, { params, observe: 'response' }).pipe(
      map((response: HttpResponse<VoiceNote[]>) => ({
        items: response.body ?? [],
        total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
      })),
    );
  }

  createNote(transcript: string, title?: string): Observable<VoiceNote> {
    return this.http.post<VoiceNote>(`${this.api}/notes`, { transcript, title, note_type: 'note' });
  }

  command(transcript: string): Observable<VoiceCommandResponse> {
    return this.http.post<VoiceCommandResponse>(`${this.api}/command`, { transcript });
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/notes/${id}`);
  }
}
