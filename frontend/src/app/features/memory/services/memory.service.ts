import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Page, toPage } from '../../../core/utils/http';

export interface MemoryItem {
  id: string;
  memory_key: string;
  memory_value: string;
  category: string;
  importance: number;
  created_at: string;
  updated_at: string;
}

export interface MemorySummary {
  total: number;
  by_category: Record<string, number>;
  top_preferences: MemoryItem[];
}

export type MemoryListResult = Page<MemoryItem>;

@Injectable({ providedIn: 'root' })
export class MemoryService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/memory`;

  list(opts?: {
    category?: string;
    limit?: number;
    offset?: number;
  }): Observable<MemoryListResult> {
    let params = new HttpParams();
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<MemoryItem[]>(`${this.api}/items`, { params, observe: 'response' }).pipe(
      map(toPage),
    );
  }

  summary(): Observable<MemorySummary> {
    return this.http.get<MemorySummary>(`${this.api}/summary`);
  }

  create(data: {
    memory_key: string;
    memory_value: string;
    category?: string;
    importance?: number;
  }): Observable<MemoryItem> {
    return this.http.post<MemoryItem>(`${this.api}/items`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/items/${id}`);
  }
}
