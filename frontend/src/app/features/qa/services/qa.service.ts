import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { QAEntry, QAListItem, QAListOptions, QAListResult } from '../models/qa.models';

interface QAWritePayload {
  question?: string;
  answer?: string;
  type?: string | null;
  tags?: string[];
  is_deep_personal?: boolean;
  linked_goal_id?: string | null;
}

@Injectable({ providedIn: 'root' })
export class QAService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/qa`;
  private readonly api = `${this.base}/entries`;

  list(opts?: QAListOptions): Observable<QAListResult> {
    let params = new HttpParams();
    if (opts?.search) params = params.set('search', opts.search);
    if (opts?.type) params = params.set('type', opts.type);
    if (opts?.tag) params = params.set('tag', opts.tag);
    if (opts?.deep_personal === true) params = params.set('deep_personal', 'true');
    if (opts?.deep_personal === false) params = params.set('deep_personal', 'false');
    if (opts?.sort_by) params = params.set('sort_by', opts.sort_by);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    if (opts?.include_answer === false) params = params.set('include_answer', 'false');
    return this.http.get<QAListItem[]>(this.api, { params, observe: 'response' }).pipe(
      map((response: HttpResponse<QAListItem[]>) => ({
        items: response.body ?? [],
        total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
      })),
    );
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

  listTypes(): Observable<string[]> {
    return this.http.get<string[]>(`${this.base}/types`);
  }

  createType(name: string): Observable<string[]> {
    return this.http.post<string[]>(`${this.base}/types`, { name });
  }
}
