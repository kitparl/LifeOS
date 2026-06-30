import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  RaceCreate,
  RaceEvent,
  Run,
  RunCreate,
  RunListItem,
  RunUpdate,
  RunningSettings,
  RunningStats,
} from '../models/running.models';

@Injectable({ providedIn: 'root' })
export class RunningService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/running`;

  listRuns(): Observable<RunListItem[]> {
    return this.http.get<RunListItem[]>(`${this.api}/runs`);
  }

  getRun(id: string): Observable<Run> {
    return this.http.get<Run>(`${this.api}/runs/${id}`);
  }

  createRun(data: RunCreate): Observable<Run> {
    return this.http.post<Run>(`${this.api}/runs`, data);
  }

  updateRun(id: string, data: RunUpdate): Observable<Run> {
    return this.http.patch<Run>(`${this.api}/runs/${id}`, data);
  }

  deleteRun(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/runs/${id}`);
  }

  listRaces(upcomingOnly = false): Observable<RaceEvent[]> {
    const params = new HttpParams().set('upcoming_only', String(upcomingOnly));
    return this.http.get<RaceEvent[]>(`${this.api}/races`, { params });
  }

  createRace(data: RaceCreate): Observable<RaceEvent> {
    return this.http.post<RaceEvent>(`${this.api}/races`, data);
  }

  deleteRace(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/races/${id}`);
  }

  getSettings(): Observable<RunningSettings> {
    return this.http.get<RunningSettings>(`${this.api}/settings`);
  }

  updateSettings(data: Partial<RunningSettings>): Observable<RunningSettings> {
    return this.http.patch<RunningSettings>(`${this.api}/settings`, data);
  }

  getStats(): Observable<RunningStats> {
    return this.http.get<RunningStats>(`${this.api}/stats`);
  }
}
