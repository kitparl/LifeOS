import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { WishlistItem, WishlistListItem } from '../models/wishlist.models';

@Injectable({ providedIn: 'root' })
export class WishlistService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/wishlist/items`;

  list(category?: string): Observable<WishlistListItem[]> {
    let params = new HttpParams();
    if (category) params = params.set('category', category);
    return this.http.get<WishlistListItem[]>(this.api, { params });
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
}
