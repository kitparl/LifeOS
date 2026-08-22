import { HttpClient, HttpErrorResponse, HttpHeaders, HttpResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { lifeosDb } from './lifeos-db';
import { SyncOperationRecord, SyncStatus } from './sync.models';

const MUTATING = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
const MAX_RETRIES = 15;
/** Client errors that replay will not fix by retrying. */
const NON_RETRYABLE_STATUSES = new Set([400, 404, 405, 409, 422]);

@Injectable({ providedIn: 'root' })
export class SyncService {
  private readonly http = inject(HttpClient);

  readonly online = signal(typeof navigator !== 'undefined' ? navigator.onLine : true);
  readonly syncing = signal(false);
  readonly pendingCount = signal(0);
  readonly lastFlushError = signal<string | null>(null);
  readonly pendingSummary = signal<string | null>(null);

  readonly status = computed<SyncStatus>(() => {
    if (!this.online()) return 'offline';
    if (this.syncing() || this.pendingCount() > 0) return 'syncing';
    return 'synced';
  });

  readonly statusDetail = computed(() => {
    const pending = this.pendingCount();
    if (pending <= 0) {
      return this.lastFlushError();
    }
    const summary = this.pendingSummary();
    const err = this.lastFlushError();
    if (summary && err) return `${summary} — ${err}`;
    return summary ?? err;
  });

  private flushTimer?: ReturnType<typeof setInterval>;

  async init(): Promise<void> {
    await this.refreshPendingCount();
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      this.online.set(true);
      void this.flush();
    });
    window.addEventListener('offline', () => this.online.set(false));

    this.flushTimer = setInterval(() => {
      if (this.online()) void this.flush();
    }, 30_000);

    if (this.online()) void this.flush();
  }

  isOnline(): boolean {
    return this.online();
  }

  shouldBypass(url: string): boolean {
    return (
      url.includes('/auth/') ||
      url.includes('/files/upload') ||
      (url.includes('/files/') && url.includes('/content')) ||
      (url.includes('/files/') && url.includes('/download-token'))
    );
  }

  isMutating(method: string): boolean {
    return MUTATING.has(method.toUpperCase());
  }

  async cacheResponse(key: string, data: unknown): Promise<void> {
    await lifeosDb.entityCache.put({ key, data, fetchedAt: Date.now() });
  }

  async getCached(key: string): Promise<unknown | null> {
    const row = await lifeosDb.entityCache.get(key);
    return row?.data ?? null;
  }

  async enqueue(method: string, url: string, body: unknown): Promise<SyncOperationRecord> {
    const op: SyncOperationRecord = {
      id: crypto.randomUUID(),
      method: method.toUpperCase(),
      url,
      body: body != null ? JSON.stringify(body) : null,
      createdAt: Date.now(),
      retries: 0,
    };
    await lifeosDb.syncOperations.add(op);
    await this.refreshPendingCount();
    return op;
  }

  buildOptimisticResponse(method: string, body: unknown): unknown {
    const now = new Date().toISOString();
    const localId = `local-${crypto.randomUUID()}`;
    if (method === 'DELETE') {
      return null;
    }
    if (body && typeof body === 'object') {
      return { ...(body as object), id: localId, created_at: now, updated_at: now };
    }
    return { id: localId, created_at: now, updated_at: now };
  }

  async refreshPendingCount(): Promise<void> {
    const ops = await lifeosDb.syncOperations.orderBy('createdAt').toArray();
    this.pendingCount.set(ops.length);
    this.pendingSummary.set(ops.length > 0 ? this.describeOp(ops[0]) : null);
    if (ops.length === 0) {
      this.lastFlushError.set(null);
    }
  }

  async flush(): Promise<void> {
    if (this.syncing() || !this.online()) return;
    const ops = await lifeosDb.syncOperations.orderBy('createdAt').toArray();
    if (ops.length === 0) return;

    this.syncing.set(true);
    try {
      for (const op of ops) {
        try {
          const body = op.body ? JSON.parse(op.body) : undefined;
          await firstValueFrom(
            this.http.request(op.method, op.url, {
              body,
              headers: new HttpHeaders({ 'X-Sync-Replay': '1' }),
              observe: 'response',
            }),
          );
          await lifeosDb.syncOperations.delete(op.id);
          this.lastFlushError.set(null);
        } catch (err) {
          const message = this.formatFlushError(op, err);
          this.lastFlushError.set(message);
          console.warn('[LifeOS sync]', message);

          if (this.shouldDropOperation(op, err)) {
            console.warn('[LifeOS sync] Dropping non-retryable operation:', this.describeOp(op));
            await lifeosDb.syncOperations.delete(op.id);
            continue;
          }

          await lifeosDb.syncOperations.update(op.id, { retries: op.retries + 1 });
          break;
        }
      }
    } finally {
      await this.refreshPendingCount();
      this.syncing.set(false);
    }
  }

  asHttpResponse<T>(body: T, status = 200): HttpResponse<T> {
    return new HttpResponse({ body, status });
  }

  private shouldDropOperation(op: SyncOperationRecord, err: unknown): boolean {
    if (err instanceof HttpErrorResponse && NON_RETRYABLE_STATUSES.has(err.status)) {
      return true;
    }
    return op.retries + 1 >= MAX_RETRIES;
  }

  private describeOp(op: SyncOperationRecord): string {
    const path = op.url.replace(/^https?:\/\/[^/]+/, '');
    return `${op.method} ${path}`;
  }

  private formatFlushError(op: SyncOperationRecord, err: unknown): string {
    const action = this.describeOp(op);
    if (err instanceof HttpErrorResponse) {
      const detail =
        typeof err.error === 'object' && err.error && 'detail' in err.error
          ? String((err.error as { detail: unknown }).detail)
          : err.statusText || 'Request failed';
      return `${action} failed (${err.status || 0}): ${detail}`;
    }
    if (err instanceof Error) {
      return `${action} failed: ${err.message}`;
    }
    return `${action} failed`;
  }
}
