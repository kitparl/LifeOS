import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Routine, RoutineCreate, RoutineListItem, RoutineUpdate } from '../models/routine.models';
import { Page, toPage } from '../../../core/utils/http';

export type RoutineListResult = Page<RoutineListItem>;

@Injectable({ providedIn: 'root' })
export class RoutinesService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/routines`;

  list(opts?: {
    activeOnly?: boolean;
    limit?: number;
    offset?: number;
  }): Observable<RoutineListResult> {
    let params = new HttpParams().set('active_only', String(opts?.activeOnly ?? true));
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<RoutineListItem[]>(this.api, { params, observe: 'response' }).pipe(
      map(toPage),
    );
  }

  get(id: string): Observable<Routine> {
    return this.http.get<Routine>(`${this.api}/${id}`);
  }

  getByBlock(blockId: string): Observable<Routine> {
    return this.http.get<Routine>(`${this.api}/by-block/${blockId}`);
  }

  create(data: RoutineCreate): Observable<Routine> {
    return this.http.post<Routine>(this.api, data);
  }

  update(id: string, data: RoutineUpdate): Observable<Routine> {
    return this.http.patch<Routine>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  listAreas(): Observable<string[]> {
    return this.http.get<string[]>(`${this.api}/areas`);
  }

  createArea(name: string): Observable<string[]> {
    return this.http.post<string[]>(`${this.api}/areas`, { name });
  }

  listCategories(): Observable<string[]> {
    return this.http.get<string[]>(`${this.api}/categories`);
  }

  createCategory(name: string): Observable<string[]> {
    return this.http.post<string[]>(`${this.api}/categories`, { name });
  }
}
