import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

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

@Injectable({ providedIn: 'root' })
export class MemoryService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/memory`;

  list(category?: string): Observable<MemoryItem[]> {
    if (category) {
      return this.http.get<MemoryItem[]>(`${this.api}/items`, { params: { category } });
    }
    return this.http.get<MemoryItem[]>(`${this.api}/items`);
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
