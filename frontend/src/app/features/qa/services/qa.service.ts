import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { QAEntry, QAListItem } from '../models/qa.models';

interface QAWritePayload {
  question?: string;
  answer?: string;
  type?: string | null;
  tags?: string[];
  linked_goal_id?: string | null;
}

@Injectable({ providedIn: 'root' })
export class QAService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/qa`;
  private readonly api = `${this.base}/entries`;

  list(search?: string, type?: string): Observable<QAListItem[]> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    if (type) params = params.set('type', type);
    return this.http.get<QAListItem[]>(this.api, { params });
  }

  get(id: string): Observable<QAEntry> {
    return this.http.get<QAEntry>(`${this.api}/${id}`);
  }

  create(data: QAWritePayload): Observable<QAEntry> {
    return this.http.post<QAEntry>(this.api, data);
  }

  update(id: string, data: QAWritePayload): Observable<QAEntry> {
    return this.http.patch<QAEntry>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  /** Extensible type registry (suggested defaults + user-created). */
  listTypes(): Observable<string[]> {
    return this.http.get<string[]>(`${this.base}/types`);
  }

  createType(name: string): Observable<string[]> {
    return this.http.post<string[]>(`${this.base}/types`, { name });
  }
}
