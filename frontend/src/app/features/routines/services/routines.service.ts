import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Routine, RoutineCreate, RoutineListItem, RoutineUpdate } from '../models/routine.models';

@Injectable({ providedIn: 'root' })
export class RoutinesService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/routines`;

  list(activeOnly = false): Observable<RoutineListItem[]> {
    const params = new HttpParams().set('active_only', String(activeOnly));
    return this.http.get<RoutineListItem[]>(this.api, { params });
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
}
