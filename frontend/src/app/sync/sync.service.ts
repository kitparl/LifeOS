import { HttpClient, HttpHeaders, HttpResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { lifeosDb } from './lifeos-db';
import { SyncOperationRecord, SyncStatus } from './sync.models';

const MUTATING = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

@Injectable({ providedIn: 'root' })
export class SyncService {
  private readonly http = inject(HttpClient);

  readonly online = signal(typeof navigator !== 'undefined' ? navigator.onLine : true);
  readonly syncing = signal(false);
  readonly pendingCount = signal(0);

  readonly status = computed<SyncStatus>(() => {
    if (!this.online()) return 'offline';
    if (this.syncing() || this.pendingCount() > 0) return 'syncing';
    return 'synced';
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
      url.includes('/files/') && url.includes('/content')
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
    const count = await lifeosDb.syncOperations.count();
    this.pendingCount.set(count);
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
        } catch {
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
}
