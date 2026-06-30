import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { LearningItem, LearningListItem } from '../models/learning.models';

@Injectable({ providedIn: 'root' })
export class LearningService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/learning/items`;

  list(itemType?: string): Observable<LearningListItem[]> {
    let params = new HttpParams();
    if (itemType) params = params.set('item_type', itemType);
    return this.http.get<LearningListItem[]>(this.api, { params });
  }

  get(id: string): Observable<LearningItem> {
    return this.http.get<LearningItem>(`${this.api}/${id}`);
  }

  create(data: Partial<LearningItem>): Observable<LearningItem> {
    return this.http.post<LearningItem>(this.api, data);
  }

  update(id: string, data: Partial<LearningItem>): Observable<LearningItem> {
    return this.http.patch<LearningItem>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }
}
