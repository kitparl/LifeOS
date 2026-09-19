import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { StickyNote, StickyNoteMonth } from '../models/sticky-note.models';

export type StickyNoteCreate = Partial<Pick<StickyNote, 'title' | 'content' | 'color' | 'is_pinned'>>;
export type StickyNoteUpdate = Partial<
  Pick<StickyNote, 'title' | 'content' | 'color' | 'is_pinned' | 'order_index'>
>;

@Injectable({ providedIn: 'root' })
export class StickyNotesService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/sticky-notes`;

  listMonths(): Observable<StickyNoteMonth[]> {
    return this.http.get<StickyNoteMonth[]>(`${this.api}/months`);
  }

  listByMonth(month: string): Observable<StickyNote[]> {
    return this.http.get<StickyNote[]>(this.api, { params: { month } });
  }

  listAll(): Observable<StickyNote[]> {
    return this.http.get<StickyNote[]>(`${this.api}/all`);
  }

  listDeleted(): Observable<StickyNote[]> {
    return this.http.get<StickyNote[]>(`${this.api}/deleted`);
  }

  listRecent(limit = 5): Observable<StickyNote[]> {
    return this.http.get<StickyNote[]>(`${this.api}/recent`, { params: { limit } });
  }

  search(query: string): Observable<StickyNote[]> {
    return this.http.get<StickyNote[]>(`${this.api}/search`, { params: { q: query } });
  }

  create(data: StickyNoteCreate): Observable<StickyNote> {
    return this.http.post<StickyNote>(this.api, data);
  }

  update(id: string, data: StickyNoteUpdate): Observable<StickyNote> {
    return this.http.patch<StickyNote>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  restore(id: string): Observable<StickyNote> {
    return this.http.post<StickyNote>(`${this.api}/${id}/restore`, {});
  }
}
