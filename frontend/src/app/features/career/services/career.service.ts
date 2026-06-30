import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

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

  listProjects(): Observable<Record<string, unknown>[]> {
    return this.http.get<Record<string, unknown>[]>(`${this.api}/projects`);
  }

  createProject(data: Record<string, unknown>): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.api}/projects`, data);
  }

  deleteProject(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/projects/${id}`);
  }

  listApplications(): Observable<Record<string, unknown>[]> {
    return this.http.get<Record<string, unknown>[]>(`${this.api}/applications`);
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
