import { Injectable, computed, signal } from '@angular/core';
import { readJsonLocalStorage, writeJsonLocalStorage } from '../../../core/services/preferences-sync';

const STORAGE_KEY = 'lifeos-dev-tools-favorites';

/** Pure-localStorage favorites for the Developer module. Stores tool IDs only — never tool content. */
@Injectable({ providedIn: 'root' })
export class DevFavoritesService {
  private readonly favorites = signal<string[]>(readJsonLocalStorage<string[]>(STORAGE_KEY, []));

  readonly favoriteIds = computed(() => this.favorites());

  isFavorite(toolId: string): boolean {
    return this.favorites().includes(toolId);
  }

  toggle(toolId: string): void {
    const current = this.favorites();
    const next = current.includes(toolId) ? current.filter((id) => id !== toolId) : [...current, toolId];
    this.favorites.set(next);
    writeJsonLocalStorage(STORAGE_KEY, next);
  }
}
