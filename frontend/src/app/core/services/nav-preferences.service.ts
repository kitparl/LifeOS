import { Injectable, computed, signal } from '@angular/core';
import {
  DEFAULT_PINNED_IDS,
  NAV_DESTINATIONS,
  NavDestination,
  getDestinationById,
} from '../../shared/layout/nav-registry';

@Injectable({ providedIn: 'root' })
export class NavPreferencesService {
  private readonly storageKey = 'lifeos-nav-pinned';

  private readonly pinnedIds = signal<string[]>(this.readStored());

  readonly pinnedDestinations = computed(() =>
    this.pinnedIds()
      .map((id) => getDestinationById(id))
      .filter((d): d is NavDestination => d !== undefined && !d.hidden),
  );

  readonly unpinnedDestinations = computed(() => {
    const pinned = new Set(this.pinnedIds());
    return NAV_DESTINATIONS.filter((d) => !pinned.has(d.id) && !d.hidden);
  });

  /** Pinned first (in order), then unpinned — for settings UI */
  readonly settingsDestinations = computed(() => [
    ...this.pinnedDestinations(),
    ...this.unpinnedDestinations(),
  ]);

  init(): void {
    this.pinnedIds.set(this.readStored());
  }

  isPinned(id: string): boolean {
    return this.pinnedIds().includes(id);
  }

  pin(id: string): void {
    if (!getDestinationById(id) || this.isPinned(id)) {
      return;
    }
    this.persist([...this.pinnedIds(), id]);
  }

  unpin(id: string): void {
    this.persist(this.pinnedIds().filter((x) => x !== id));
  }

  togglePin(id: string): void {
    if (this.isPinned(id)) {
      this.unpin(id);
    } else {
      this.pin(id);
    }
  }

  reorder(fromIndex: number, toIndex: number): void {
    const ids = [...this.pinnedIds()];
    if (fromIndex < 0 || fromIndex >= ids.length || toIndex < 0 || toIndex >= ids.length) {
      return;
    }
    const [moved] = ids.splice(fromIndex, 1);
    ids.splice(toIndex, 0, moved);
    this.persist(ids);
  }

  setPinnedOrder(ids: string[]): void {
    const valid = ids.filter((id) => getDestinationById(id) !== undefined && this.isPinned(id));
    const remaining = this.pinnedIds().filter((id) => !valid.includes(id));
    this.persist([...valid, ...remaining]);
  }

  moveUp(id: string): void {
    const ids = this.pinnedIds();
    const index = ids.indexOf(id);
    if (index > 0) {
      this.reorder(index, index - 1);
    }
  }

  moveDown(id: string): void {
    const ids = this.pinnedIds();
    const index = ids.indexOf(id);
    if (index >= 0 && index < ids.length - 1) {
      this.reorder(index, index + 1);
    }
  }

  resetToDefault(): void {
    this.persist([...DEFAULT_PINNED_IDS]);
  }

  private persist(ids: string[]): void {
    const valid = ids.filter((id) => getDestinationById(id) !== undefined);
    this.pinnedIds.set(valid);
    localStorage.setItem(this.storageKey, JSON.stringify(valid));
  }

  private readStored(): string[] {
    try {
      const raw = localStorage.getItem(this.storageKey);
      if (!raw) {
        return [...DEFAULT_PINNED_IDS];
      }
      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) {
        return [...DEFAULT_PINNED_IDS];
      }
      const valid = parsed.filter((id): id is string => typeof id === 'string' && getDestinationById(id) !== undefined);
      return valid.length > 0 ? valid : [...DEFAULT_PINNED_IDS];
    } catch {
      return [...DEFAULT_PINNED_IDS];
    }
  }
}
