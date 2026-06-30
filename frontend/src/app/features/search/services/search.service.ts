import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { SearchResponse } from '../models/search.models';

@Injectable({ providedIn: 'root' })
export class SearchService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/search`;

  search(q: string, limit = 20): Observable<SearchResponse> {
    const params = new HttpParams().set('q', q).set('limit', String(limit));
    return this.http.get<SearchResponse>(this.api, { params });
  }
}
