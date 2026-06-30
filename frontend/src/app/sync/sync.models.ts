export type SyncStatus = 'synced' | 'syncing' | 'offline';

export interface SyncOperationRecord {
  id: string;
  method: string;
  url: string;
  body: string | null;
  createdAt: number;
  retries: number;
}

export interface EntityCacheRecord {
  key: string;
  data: unknown;
  fetchedAt: number;
}
