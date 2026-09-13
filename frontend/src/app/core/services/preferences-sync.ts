import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export function readJsonLocalStorage<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function writeJsonLocalStorage(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore quota / private mode */
  }
}

/** Thin GET/PUT helper for `${apiUrl}/preferences/${key}`. */
export class PreferencesApi {
  private readonly base = `${environment.apiUrl}/preferences`;

  constructor(private readonly http: HttpClient) {}

  get<T>(key: string): Observable<{ key: string; value: T | null }> {
    return this.http.get<{ key: string; value: T | null }>(`${this.base}/${key}`);
  }

  put(key: string, value: unknown): Observable<unknown> {
    return this.http.put(`${this.base}/${key}`, { value });
  }
}
