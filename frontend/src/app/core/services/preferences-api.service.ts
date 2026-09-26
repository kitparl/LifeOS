import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

/** GET/PUT for `${apiUrl}/preferences/${key}` (the per-user preference store). */
@Injectable({ providedIn: 'root' })
export class PreferencesApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/preferences`;

  get<T>(key: string): Observable<{ key: string; value: T | null }> {
    return this.http.get<{ key: string; value: T | null }>(`${this.base}/${key}`);
  }

  put(key: string, value: unknown): Observable<unknown> {
    return this.http.put(`${this.base}/${key}`, { value });
  }
}
