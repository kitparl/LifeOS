import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { JournalCreate, JournalEntry, JournalListItem, JournalUpdate } from '../models/journal.models';

@Injectable({ providedIn: 'root' })
export class JournalService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/journal/entries`;

  list(entryType?: string, search?: string): Observable<JournalListItem[]> {
    let params = new HttpParams();
    if (entryType) params = params.set('entry_type', entryType);
    if (search) params = params.set('search', search);
    return this.http.get<JournalListItem[]>(this.api, { params });
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
