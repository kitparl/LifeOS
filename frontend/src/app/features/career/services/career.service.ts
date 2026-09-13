import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface CareerListResult {
  items: Record<string, unknown>[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class CareerService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/career`;

  getProfile(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.api}/profile`);
  }

  updateProfile(data: Record<string, unknown>): Observable<Record<string, unknown>> {
    return this.http.patch<Record<string, unknown>>(`${this.api}/profile`, data);
  }

  listProjects(opts?: { limit?: number; offset?: number }): Observable<CareerListResult> {
    let params = new HttpParams();
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http
      .get<Record<string, unknown>[]>(`${this.api}/projects`, { params, observe: 'response' })
      .pipe(
        map((response: HttpResponse<Record<string, unknown>[]>) => ({
          items: response.body ?? [],
          total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
        })),
      );
  }

  createProject(data: Record<string, unknown>): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.api}/projects`, data);
  }

  deleteProject(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/projects/${id}`);
  }

  listApplications(opts?: { limit?: number; offset?: number }): Observable<CareerListResult> {
    let params = new HttpParams();
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http
      .get<Record<string, unknown>[]>(`${this.api}/applications`, { params, observe: 'response' })
      .pipe(
        map((response: HttpResponse<Record<string, unknown>[]>) => ({
          items: response.body ?? [],
          total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
        })),
      );
  }

  createApplication(data: Record<string, unknown>): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.api}/applications`, data);
  }

  deleteApplication(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/applications/${id}`);
  }

  analytics(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.api}/analytics`);
  }
}
