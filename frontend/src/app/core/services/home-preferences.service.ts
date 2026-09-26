import { Injectable, computed, inject, signal } from '@angular/core';
import {
  DEFAULT_HOME_MODULE_ID,
  groupedHomeDestinations,
  homeRouteFor,
  isAvailableHomeModule,
} from '../../shared/layout/nav-registry';
import {
  readJsonLocalStorage,
  writeJsonLocalStorage,
} from './preferences-sync';
import { PreferencesApiService } from './preferences-api.service';

export interface HomePrefsValue {
  moduleId: string;
}

const STORAGE_KEY = 'lifeos-home-prefs';
const PREFS_KEY = 'home';
const DEFAULT_PREFS: HomePrefsValue = { moduleId: DEFAULT_HOME_MODULE_ID };

function normalizePrefs(raw: unknown): HomePrefsValue {
  if (raw && typeof raw === 'object' && 'moduleId' in raw) {
    const id = (raw as HomePrefsValue).moduleId;
    if (typeof id === 'string' && isAvailableHomeModule(id)) {
      return { moduleId: id };
    }
  }
  if (typeof raw === 'string' && isAvailableHomeModule(raw)) {
    return { moduleId: raw };
  }
  return { ...DEFAULT_PREFS };
}

@Injectable({ providedIn: 'root' })
export class HomePreferencesService {
  private readonly prefsApi = inject(PreferencesApiService);

  /** Seed from localStorage immediately so `/` can redirect before init(). */
  private readonly prefs = signal<HomePrefsValue>(this.readLocal());

  readonly moduleId = computed(() => this.prefs().moduleId);
  readonly homeRoute = computed(() => homeRouteFor(this.moduleId()));
  readonly groupedOptions = groupedHomeDestinations();

  init(): void {
    this.applyPrefs(this.readLocal());

    this.prefsApi.get<HomePrefsValue>(PREFS_KEY).subscribe({
      next: (resp) => {
        if (resp.value != null) {
          const normalized = normalizePrefs(resp.value);
          this.applyPrefs(normalized);
          this.cacheLocal(normalized);
        }
      },
      error: () => {
        // Offline / unauthenticated — keep local seed
      },
    });
  }

  setModuleId(moduleId: string): void {
    this.commit({ moduleId });
  }

  private applyPrefs(value: HomePrefsValue): void {
    this.prefs.set(normalizePrefs(value));
  }

  private commit(value: HomePrefsValue): void {
    const normalized = normalizePrefs(value);
    this.applyPrefs(normalized);
    this.cacheLocal(normalized);
    this.saveToApi(normalized);
  }

  private saveToApi(value: HomePrefsValue): void {
    this.prefsApi.put(PREFS_KEY, value).subscribe({ error: () => undefined });
  }

  private cacheLocal(value: HomePrefsValue): void {
    writeJsonLocalStorage(STORAGE_KEY, value);
  }

  private readLocal(): HomePrefsValue {
    return normalizePrefs(readJsonLocalStorage<unknown>(STORAGE_KEY, DEFAULT_PREFS));
  }
}
