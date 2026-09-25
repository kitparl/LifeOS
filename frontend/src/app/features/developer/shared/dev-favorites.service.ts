import { Injectable, computed, inject, signal } from '@angular/core';
import { readJsonLocalStorage, writeJsonLocalStorage } from '../../../core/services/preferences-sync';
import { DEV_TOOLS_STORAGE_SCOPE, scopedStorageName } from './dev-storage-scope';

const STORAGE_KEY = 'lifeos-dev-tools-favorites';

/** Pure-localStorage favorites for the Developer module. Stores tool IDs only — never tool content. */
@Injectable({ providedIn: 'root' })
export class DevFavoritesService {
  private readonly storageKey = scopedStorageName(STORAGE_KEY, inject(DEV_TOOLS_STORAGE_SCOPE));
  private readonly favorites = signal<string[]>(readJsonLocalStorage<string[]>(this.storageKey, []));

  readonly favoriteIds = computed(() => this.favorites());

  isFavorite(toolId: string): boolean {
    return this.favorites().includes(toolId);
  }

  toggle(toolId: string): void {
    const current = this.favorites();
    const next = current.includes(toolId) ? current.filter((id) => id !== toolId) : [...current, toolId];
    this.favorites.set(next);
    writeJsonLocalStorage(this.storageKey, next);
  }
}
