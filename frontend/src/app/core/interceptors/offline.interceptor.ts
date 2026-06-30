import {
  HttpErrorResponse,
  HttpEvent,
  HttpInterceptorFn,
  HttpResponse,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, from, of, throwError } from 'rxjs';
import { catchError, switchMap, tap } from 'rxjs';
import { SyncService } from '../../sync/sync.service';

export const offlineInterceptor: HttpInterceptorFn = (req, next) => {
  const sync = inject(SyncService);

  if (req.headers.has('X-Sync-Replay') || sync.shouldBypass(req.url)) {
    return next(req);
  }

  if (req.method === 'GET') {
    if (!sync.isOnline()) {
      return from(sync.getCached(req.urlWithParams)).pipe(
        switchMap((cached) => {
          if (cached != null) {
            return of(sync.asHttpResponse(cached));
          }
          return throwError(
            () => new HttpErrorResponse({ status: 0, statusText: 'Offline', url: req.url }),
          );
        }),
      );
    }
    return next(req).pipe(
      tap((event) => {
        if (event instanceof HttpResponse && event.body != null) {
          void sync.cacheResponse(req.urlWithParams, event.body);
        }
      }),
    );
  }

  if (!sync.isMutating(req.method)) {
    return next(req);
  }

  const queueIfOffline = (): Observable<HttpEvent<unknown>> =>
    from(sync.enqueue(req.method, req.url, req.body)).pipe(
      switchMap(() => {
        const optimistic = sync.buildOptimisticResponse(req.method, req.body);
        const status = req.method === 'DELETE' ? 204 : req.method === 'POST' ? 201 : 200;
        return of(sync.asHttpResponse(optimistic, status));
      }),
    );

  if (!sync.isOnline()) {
    return queueIfOffline();
  }

  return next(req).pipe(
    catchError((err: unknown) => {
      if (err instanceof HttpErrorResponse && (err.status === 0 || err.status >= 500)) {
        return queueIfOffline();
      }
      return throwError(() => err);
    }),
  );
};
