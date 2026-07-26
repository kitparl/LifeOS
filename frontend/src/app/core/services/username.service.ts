import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  PublicUser,
  UsernameAvailability,
  UsernameChangeRequest,
  UsernameHistoryEntry,
  User,
} from '../models/auth.models';

@Injectable({ providedIn: 'root' })
export class UsernameService {
  private readonly http = inject(HttpClient);
  private readonly authApi = `${environment.apiUrl}/auth`;
  private readonly usersApi = `${environment.apiUrl}/users`;

  checkAvailability(username: string): Observable<UsernameAvailability> {
    const params = new HttpParams().set('username', username);
    return this.http.get<UsernameAvailability>(`${this.authApi}/username-available`, { params });
  }

  changeUsername(data: UsernameChangeRequest): Observable<User> {
    return this.http.patch<User>(`${this.authApi}/me/username`, data);
  }

  history(): Observable<UsernameHistoryEntry[]> {
    return this.http.get<UsernameHistoryEntry[]>(`${this.authApi}/me/username-history`);
  }

  search(q: string, limit = 20): Observable<PublicUser[]> {
    const params = new HttpParams().set('q', q).set('limit', String(limit));
    return this.http.get<PublicUser[]>(`${this.usersApi}/search`, { params });
  }
}
