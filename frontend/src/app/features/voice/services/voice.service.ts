import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
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

@Injectable({ providedIn: 'root' })
export class VoiceService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/voice`;

  list(): Observable<VoiceNote[]> {
    return this.http.get<VoiceNote[]>(`${this.api}/notes`);
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
