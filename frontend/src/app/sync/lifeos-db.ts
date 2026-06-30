import Dexie, { type Table } from 'dexie';
import { EntityCacheRecord, SyncOperationRecord } from './sync.models';

export class LifeOSDatabase extends Dexie {
  syncOperations!: Table<SyncOperationRecord, string>;
  entityCache!: Table<EntityCacheRecord, string>;

  constructor() {
    super('LifeOS');
    this.version(1).stores({
      syncOperations: 'id, createdAt',
      entityCache: 'key, fetchedAt',
    });
  }
}

export const lifeosDb = new LifeOSDatabase();
