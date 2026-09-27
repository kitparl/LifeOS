import { Injectable, signal } from '@angular/core';
import { DeviceSplitGroup, SplitRole } from '../models/split.models';

export const SPLIT_DEVICE_STORAGE_KEY = 'lifeos-split-groups';

const ROLES: readonly SplitRole[] = ['creator', 'member'];

function isDeviceGroup(value: unknown): value is DeviceSplitGroup {
  if (!value || typeof value !== 'object') return false;
  const row = value as Record<string, unknown>;
  return (
    typeof row['code'] === 'string' &&
    typeof row['name'] === 'string' &&
    typeof row['seatSecret'] === 'string' &&
    typeof row['displayName'] === 'string' &&
    ROLES.includes(row['role'] as SplitRole)
  );
}

/**
 * Groups this browser created or joined, with their seat secrets. It is how a guest
 * finds a link again; clearing site data removes it (the link itself still works).
 */
@Injectable({ providedIn: 'root' })
export class SplitDeviceStoreService {
  private readonly rows = signal<DeviceSplitGroup[]>(this.read());

  readonly groups = this.rows.asReadonly();

  find(code: string): DeviceSplitGroup | undefined {
    return this.rows().find((row) => row.code === code);
  }

  /** Newest first; a repeat code replaces its old row. */
  save(group: DeviceSplitGroup): void {
    const next = [group, ...this.rows().filter((row) => row.code !== group.code)];
    this.rows.set(next);
    try {
      localStorage.setItem(SPLIT_DEVICE_STORAGE_KEY, JSON.stringify(next));
    } catch {
      // Storage full or blocked — the in-memory list still works for this visit.
    }
  }

  private read(): DeviceSplitGroup[] {
    try {
      const parsed: unknown = JSON.parse(localStorage.getItem(SPLIT_DEVICE_STORAGE_KEY) ?? '[]');
      return Array.isArray(parsed) ? parsed.filter(isDeviceGroup) : [];
    } catch {
      return [];
    }
  }
}
