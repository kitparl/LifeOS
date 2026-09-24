import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

const AUTH_SKIP_REFRESH = [
  '/auth/login',
  '/auth/google',
  '/auth/register',
  '/auth/refresh',
  '/auth/logout',
  '/auth/registration-gate/',
  '/auth/admin/create-user',
];

function shouldSkipRefresh(url: string): boolean {
  return AUTH_SKIP_REFRESH.some((path) => url.includes(path));
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const token = auth.getToken();

  let authReq = req;
  if (token && !req.headers.has('Authorization')) {
    authReq = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }

  return next(authReq).pipe(
    catchError((err: unknown) => {
      if (!(err instanceof HttpErrorResponse) || err.status !== 401) {
        return throwError(() => err);
      }
      // No in-memory token → guest page (e.g. /register-access). Refresh-on-401
      // would call clearSession() and bounce to /login.
      if (!token || shouldSkipRefresh(req.url) || req.headers.has('X-Retry')) {
        return throwError(() => err);
      }

      // auth.refresh() is single-flight — concurrent 401s share one refresh call
      return auth.refresh().pipe(
        switchMap((newToken) => {
          const retry = authReq.clone({
            setHeaders: {
              Authorization: `Bearer ${newToken}`,
              'X-Retry': '1',
            },
          });
          return next(retry);
        }),
        catchError((refreshErr) => throwError(() => refreshErr)),
      );
    }),
  );
};
