import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  RaceCreate,
  RaceEvent,
  RaceUpdate,
  Run,
  RunCreate,
  RunListItem,
  RunUpdate,
  RunningSettings,
  RunningStats,
} from '../models/running.models';
import { toPage } from '../../../core/utils/http';

@Injectable({ providedIn: 'root' })
export class RunningService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/running`;

  listRuns(opts?: {
    shoe?: string;
    limit?: number;
    offset?: number;
  }): Observable<{ items: RunListItem[]; total: number }> {
    let params = new HttpParams();
    if (opts?.shoe) params = params.set('shoe', opts.shoe);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<RunListItem[]>(`${this.api}/runs`, { params, observe: 'response' }).pipe(
      map(toPage),
    );
  }

  listShoes(): Observable<string[]> {
    return this.http.get<string[]>(`${this.api}/shoes`);
  }

  createShoe(name: string): Observable<string[]> {
    return this.http.post<string[]>(`${this.api}/shoes`, { name });
  }

  listAccreditations(): Observable<string[]> {
    return this.http.get<string[]>(`${this.api}/accreditations`);
  }

  createAccreditation(name: string): Observable<string[]> {
    return this.http.post<string[]>(`${this.api}/accreditations`, { name });
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

  getRace(id: string): Observable<RaceEvent> {
    return this.http.get<RaceEvent>(`${this.api}/races/${id}`);
  }

  createRace(data: RaceCreate): Observable<RaceEvent> {
    return this.http.post<RaceEvent>(`${this.api}/races`, data);
  }

  updateRace(id: string, data: RaceUpdate): Observable<RaceEvent> {
    return this.http.patch<RaceEvent>(`${this.api}/races/${id}`, data);
  }

  deleteRace(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/races/${id}`);
  }

  listRaceCandidates(raceId: string): Observable<RunListItem[]> {
    return this.http.get<RunListItem[]>(`${this.api}/races/${raceId}/candidates`);
  }

  attachRun(raceId: string, runId: string): Observable<RaceEvent> {
    return this.http.put<RaceEvent>(`${this.api}/races/${raceId}/attachment`, { run_id: runId });
  }

  detachRun(raceId: string): Observable<RaceEvent> {
    return this.http.delete<RaceEvent>(`${this.api}/races/${raceId}/attachment`);
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
