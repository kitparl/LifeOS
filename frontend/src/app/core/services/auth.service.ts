import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import {
  Observable,
  Subject,
  catchError,
  map,
  of,
  share,
  switchMap,
  tap,
  throwError,
} from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
  UserUpdateRequest,
} from '../models/auth.models';

/** How many ms before expiry to proactively refresh (2 minutes) */
const REFRESH_BEFORE_MS = 2 * 60 * 1000;
/** Access token lifetime in ms (30 min - 2 min buffer = 28 min) */
const TOKEN_LIFETIME_MS = 28 * 60 * 1000;

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  /** In-memory access token — NEVER stored in sessionStorage/localStorage */
  private readonly accessToken = signal<string | null>(null);
  readonly user = signal<User | null>(null);

  /** True once the bootstrap refresh attempt has completed (success or fail) */
  readonly authReady = signal(false);

  readonly isAuthenticated = computed(() => !!this.accessToken());

  /** Single-flight subject: ongoing refresh observable shared across concurrent 401s */
  private refreshInFlight$: Observable<string> | null = null;

  private refreshTimer?: ReturnType<typeof setTimeout>;

  /** Called once at app startup via APP_INITIALIZER */
  bootstrap(): Promise<void> {
    return new Promise<void>((resolve) => {
      this.attemptRefresh()
        .pipe(
          switchMap(() => this.loadMe()),
          catchError(() => of(null)),
        )
        .subscribe({
          complete: () => {
            this.authReady.set(true);
            this.scheduleProactiveRefresh();
            this.setupVisibilityRefresh();
            resolve();
          },
          error: () => {
            this.authReady.set(true);
            resolve();
          },
        });
    });
  }

  login(data: LoginRequest): Observable<User> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, data, {
        withCredentials: true,
      })
      .pipe(
        tap((res) => this.setToken(res.access_token)),
        switchMap(() => this.loadMe()),
        map(() => this.user()!),
        tap(() => this.scheduleProactiveRefresh()),
        catchError((err) => throwError(() => err)),
      );
  }

  register(data: RegisterRequest): Observable<User> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/register`, data, {
        withCredentials: true,
      })
      .pipe(
        tap((res) => this.setToken(res.access_token)),
        switchMap(() => this.loadMe()),
        map(() => this.user()!),
        tap(() => this.scheduleProactiveRefresh()),
        catchError((err) => throwError(() => err)),
      );
  }

  logout(): Observable<void> {
    this.cancelRefreshTimer();
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
    if (!this.accessToken()) return of(null);
    return this.http.get<User>(`${environment.apiUrl}/auth/me`).pipe(
      tap((u) => this.user.set(u)),
      catchError(() => of(null)),
    );
  }

  updateProfile(data: UserUpdateRequest): Observable<User> {
    return this.http
      .patch<User>(`${environment.apiUrl}/auth/me`, data)
      .pipe(tap((u) => this.user.set(u)));
  }

  changePassword(currentPassword: string, newPassword: string): Observable<void> {
    return this.http.post<void>(`${environment.apiUrl}/auth/me/change-password`, {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  getToken(): string | null {
    return this.accessToken();
  }

  /**
   * Single-flight refresh — multiple concurrent callers share the same request.
   * Returns the new access token on success; throws on failure (triggers logout).
   */
  refresh(): Observable<string> {
    if (this.refreshInFlight$) return this.refreshInFlight$;

    this.refreshInFlight$ = this.attemptRefresh().pipe(
      tap(() => {
        this.refreshInFlight$ = null;
        this.scheduleProactiveRefresh();
      }),
      catchError((err) => {
        this.refreshInFlight$ = null;
        this.clearSession();
        return throwError(() => err);
      }),
      share(),
    );
    return this.refreshInFlight$;
  }

  private attemptRefresh(): Observable<string> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/refresh`, {}, { withCredentials: true })
      .pipe(
        tap((res) => this.setToken(res.access_token)),
        map((res) => res.access_token),
      );
  }

  private setToken(token: string): void {
    this.accessToken.set(token);
  }

  clearSession(): void {
    this.cancelRefreshTimer();
    this.accessToken.set(null);
    this.user.set(null);
    this.router.navigate(['/login']);
  }

  private scheduleProactiveRefresh(): void {
    this.cancelRefreshTimer();
    this.refreshTimer = setTimeout(() => {
      this.attemptRefresh()
        .pipe(
          catchError(() => of(null)),
          switchMap(() => this.loadMe()),
          catchError(() => of(null)),
        )
        .subscribe({ complete: () => this.scheduleProactiveRefresh() });
    }, TOKEN_LIFETIME_MS);
  }

  private cancelRefreshTimer(): void {
    if (this.refreshTimer !== undefined) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = undefined;
    }
  }

  private setupVisibilityRefresh(): void {
    if (typeof document === 'undefined') return;
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && this.isAuthenticated()) {
        this.attemptRefresh()
          .pipe(catchError(() => of(null)))
          .subscribe();
      }
    });
  }
}
