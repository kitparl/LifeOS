import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { JournalCreate, JournalEntry, JournalListItem, JournalUpdate } from '../models/journal.models';

export interface JournalListResult {
  items: JournalListItem[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class JournalService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/journal/entries`;

  list(opts?: {
    entryType?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Observable<JournalListResult> {
    let params = new HttpParams();
    if (opts?.entryType) params = params.set('entry_type', opts.entryType);
    if (opts?.search) params = params.set('search', opts.search);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<JournalListItem[]>(this.api, { params, observe: 'response' }).pipe(
      map((response: HttpResponse<JournalListItem[]>) => ({
        items: response.body ?? [],
        total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
      })),
    );
  }

  get(id: string): Observable<JournalEntry> {
    return this.http.get<JournalEntry>(`${this.api}/${id}`);
  }

  create(data: JournalCreate): Observable<JournalEntry> {
    return this.http.post<JournalEntry>(this.api, data);
  }

  update(id: string, data: JournalUpdate): Observable<JournalEntry> {
    return this.http.patch<JournalEntry>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }
}
