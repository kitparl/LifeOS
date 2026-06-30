import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { MoodEntry, MoodStats, MoodUpsert } from '../models/mood.models';

@Injectable({ providedIn: 'root' })
export class MoodService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/mood`;

  getToday(): Observable<MoodEntry | null> {
    return this.http.get<MoodEntry | null>(`${this.api}/today`);
  }

  upsertToday(data: MoodUpsert): Observable<MoodEntry> {
    return this.http.put<MoodEntry>(`${this.api}/today`, data);
  }

  getStats(days = 7): Observable<MoodStats> {
    const params = new HttpParams().set('days', String(days));
    return this.http.get<MoodStats>(`${this.api}/stats`, { params });
  }

  list(days = 30): Observable<MoodEntry[]> {
    const params = new HttpParams().set('days', String(days));
    return this.http.get<MoodEntry[]>(`${this.api}/entries`, { params });
  }
}
