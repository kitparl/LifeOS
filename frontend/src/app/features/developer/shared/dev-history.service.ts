import { Injectable, Signal, WritableSignal, inject, signal } from '@angular/core';
import Dexie, { Table } from 'dexie';
import { DEV_TOOLS_STORAGE_SCOPE, scopedStorageName } from './dev-storage-scope';

export interface DevHistoryEntry {
  id?: number;
  toolId: string;
  input: string;
  output: string;
  createdAt: string;
}

/**
 * Tools that generate or inspect secrets/credentials — excluded from history even if a caller
 * forgets to check, per the module's privacy principle (no sensitive content ever persisted).
 */
export const HISTORY_EXCLUDED_TOOL_IDS = new Set([
  'password-generator',
  'password-strength-checker',
  'api-key-generator',
  'jwt-decoder',
  'hash-generator',
  'hmac-generator',
  'sri-hash-generator',
]);

const RETENTION_DAYS = 30;
const MAX_ENTRIES_PER_TOOL = 200;

class DevHistoryDatabase extends Dexie {
  entries!: Table<DevHistoryEntry, number>;

  constructor(name: string) {
    super(name);
    this.version(1).stores({ entries: '++id, toolId, createdAt' });
  }
}

/**
 * Per-tool history, stored in IndexedDB (via Dexie) — never sent to a server. Entries older than
 * 30 days are pruned automatically, and each tool is capped at 200 entries (oldest evicted first)
 * so storage size and load time never grow unbounded — the client-side equivalent of "switch to a
 * database-based solution" the requirement asks for, without touching the backend.
 */
@Injectable({ providedIn: 'root' })
export class DevHistoryService {
  private readonly db = new DevHistoryDatabase(scopedStorageName('DevToolsHistoryDB', inject(DEV_TOOLS_STORAGE_SCOPE)));
  private readonly cache = new Map<string, WritableSignal<DevHistoryEntry[]>>();

  getHistory(toolId: string): Signal<DevHistoryEntry[]> {
    let sig = this.cache.get(toolId);
    if (!sig) {
      sig = signal<DevHistoryEntry[]>([]);
      this.cache.set(toolId, sig);
      void this.refresh(toolId);
    }
    return sig.asReadonly();
  }

  async addEntry(toolId: string, input: string, output: string): Promise<void> {
    if (HISTORY_EXCLUDED_TOOL_IDS.has(toolId)) return;
    if (!input.trim() && !output.trim()) return;
    await this.db.entries.add({ toolId, input, output, createdAt: new Date().toISOString() });
    await this.enforceLimit(toolId);
    await this.refresh(toolId);
  }

  async deleteEntry(toolId: string, id: number): Promise<void> {
    await this.db.entries.delete(id);
    await this.refresh(toolId);
  }

  async clearHistory(toolId: string): Promise<void> {
    await this.db.entries.where('toolId').equals(toolId).delete();
    await this.refresh(toolId);
  }

  private async refresh(toolId: string): Promise<void> {
    await this.pruneOld();
    const sig = this.cache.get(toolId);
    if (!sig) return;
    const rows = await this.db.entries.where('toolId').equals(toolId).sortBy('createdAt');
    sig.set(rows.reverse());
  }

  private async pruneOld(): Promise<void> {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - RETENTION_DAYS);
    await this.db.entries.where('createdAt').below(cutoff.toISOString()).delete();
  }

  private async enforceLimit(toolId: string): Promise<void> {
    const rows = await this.db.entries.where('toolId').equals(toolId).sortBy('createdAt');
    if (rows.length > MAX_ENTRIES_PER_TOOL) {
      const excess = rows.slice(0, rows.length - MAX_ENTRIES_PER_TOOL).map((r) => r.id!);
      await this.db.entries.bulkDelete(excess);
    }
  }
}
