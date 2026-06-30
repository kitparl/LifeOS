import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, map, of, tap, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  UserUpdateRequest,
} from '../models/auth.models';

const TOKEN_KEY = 'lifeos_access_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private readonly accessToken = signal<string | null>(this.readStoredToken());
  readonly user = signal<User | null>(null);

  readonly isAuthenticated = computed(() => !!this.accessToken());

  constructor() {
    if (this.accessToken()) {
      this.loadMe().subscribe();
    }
  }

  register(data: RegisterRequest): Observable<User> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/register`, data, {
        withCredentials: true,
      })
      .pipe(
        tap((res) => this.persistToken(res.access_token)),
        map(() => this.user()!),
        catchError((err) => throwError(() => err)),
      );
  }

  login(data: LoginRequest): Observable<User> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, data, {
        withCredentials: true,
      })
      .pipe(
        tap((res) => this.persistToken(res.access_token)),
        map(() => this.user()!),
        catchError((err) => throwError(() => err)),
      );
  }

  logout(): Observable<void> {
    return this.http
      .post<{ ok: boolean }>(`${environment.apiUrl}/auth/logout`, {}, { withCredentials: true })
      .pipe(
        tap(() => this.clearSession()),
        map(() => undefined),
        catchError(() => {
          this.clearSession();
          return of(undefined);
        }),
      );
  }

  loadMe(): Observable<User | null> {
    if (!this.accessToken()) {
      return of(null);
    }
    return this.http.get<User>(`${environment.apiUrl}/auth/me`).pipe(
      tap((u) => this.user.set(u)),
      catchError(() => {
        this.clearSession();
        return of(null);
      }),
    );
  }

  updateProfile(data: UserUpdateRequest): Observable<User> {
    return this.http.patch<User>(`${environment.apiUrl}/auth/me`, data).pipe(
      tap((u) => this.user.set(u)),
    );
  }

  refresh(): Observable<string> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/refresh`, {}, { withCredentials: true })
      .pipe(
        tap((res) => this.persistToken(res.access_token)),
        map((res) => res.access_token),
        catchError((err) => {
          this.clearSession();
          return throwError(() => err);
        }),
      );
  }

  getToken(): string | null {
    return this.accessToken();
  }

  persistToken(token: string): void {
    this.accessToken.set(token);
    sessionStorage.setItem(TOKEN_KEY, token);
    this.loadMe().subscribe();
  }

  clearSession(): void {
    this.accessToken.set(null);
    this.user.set(null);
    sessionStorage.removeItem(TOKEN_KEY);
  }

  private readStoredToken(): string | null {
    if (typeof sessionStorage === 'undefined') {
      return null;
    }
    return sessionStorage.getItem(TOKEN_KEY);
  }
}
