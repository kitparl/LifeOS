import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { WishlistItem, WishlistListItem, WishlistStatusFilter } from '../models/wishlist.models';

export interface WishlistListResult {
  items: WishlistListItem[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class WishlistService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/wishlist`;
  private readonly api = `${this.base}/items`;

  list(opts?: {
    category?: string;
    status?: WishlistStatusFilter;
    limit?: number;
    offset?: number;
  }): Observable<WishlistListResult> {
    let params = new HttpParams();
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.status) params = params.set('status', opts.status);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<WishlistListItem[]>(this.api, { params, observe: 'response' }).pipe(
      map((response: HttpResponse<WishlistListItem[]>) => ({
        items: response.body ?? [],
        total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
      })),
    );
  }

  get(id: string): Observable<WishlistItem> {
    return this.http.get<WishlistItem>(`${this.api}/${id}`);
  }

  create(data: Partial<WishlistItem>): Observable<WishlistItem> {
    return this.http.post<WishlistItem>(this.api, data);
  }

  update(id: string, data: Partial<WishlistItem>): Observable<WishlistItem> {
    return this.http.patch<WishlistItem>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  listCategories(): Observable<string[]> {
    return this.http.get<string[]>(`${this.base}/categories`);
  }

  createCategory(name: string): Observable<string[]> {
    return this.http.post<string[]>(`${this.base}/categories`, { name });
  }
}
