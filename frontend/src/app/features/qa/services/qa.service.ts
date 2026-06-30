import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { QAEntry, QAListItem } from '../models/qa.models';

@Injectable({ providedIn: 'root' })
export class QAService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/qa/entries`;

  list(search?: string): Observable<QAListItem[]> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    return this.http.get<QAListItem[]>(this.api, { params });
  }

  get(id: string): Observable<QAEntry> {
    return this.http.get<QAEntry>(`${this.api}/${id}`);
  }

  create(data: { question: string; answer: string; tags?: string[] }): Observable<QAEntry> {
    return this.http.post<QAEntry>(this.api, data);
  }

  update(
    id: string,
    data: { question?: string; answer?: string; tags?: string[]; linked_goal_id?: string | null }
  ): Observable<QAEntry> {
    return this.http.patch<QAEntry>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }
}
