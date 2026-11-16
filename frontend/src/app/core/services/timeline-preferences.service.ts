import { Injectable, inject, signal } from '@angular/core';
import { readJsonLocalStorage, writeJsonLocalStorage } from './preferences-sync';
import { PreferencesApiService } from './preferences-api.service';

/**
 * Per-source on/off overrides for the Timeline. Only explicit user choices are stored, so a
 * source added later falls back to its backend `default_enabled` instead of being hidden.
 */
export type TimelineSourceOverrides = Record<string, boolean>;

interface TimelinePrefsValue {
  sources: TimelineSourceOverrides;
}

const STORAGE_KEY = 'lifeos-timeline-prefs';
const PREFS_KEY = 'timeline';

function normalizePrefs(raw: unknown): TimelinePrefsValue {
  const sources: TimelineSourceOverrides = {};
  const rawSources = raw && typeof raw === 'object' ? (raw as Partial<TimelinePrefsValue>).sources : null;
  if (rawSources && typeof rawSources === 'object') {
    for (const [key, value] of Object.entries(rawSources)) {
      if (typeof value === 'boolean') sources[key] = value;
    }
  }
  return { sources };
}

@Injectable({ providedIn: 'root' })
export class TimelinePreferencesService {
  private readonly prefsApi = inject(PreferencesApiService);

  /** Seeded from localStorage so the Timeline renders with the right sources before init() resolves. */
  readonly overrides = signal<TimelineSourceOverrides>(this.readLocal().sources);

  init(): void {
    this.prefsApi.get<TimelinePrefsValue>(PREFS_KEY).subscribe({
      next: (resp) => {
        if (resp.value && typeof resp.value === 'object') {
          const normalized = normalizePrefs(resp.value);
          this.overrides.set(normalized.sources);
          writeJsonLocalStorage(STORAGE_KEY, normalized);
        }
      },
      error: () => {
        // Offline / unauthenticated — keep local seed
      },
    });
  }

  setSourceEnabled(key: string, enabled: boolean): void {
    const value: TimelinePrefsValue = { sources: { ...this.overrides(), [key]: enabled } };
    this.overrides.set(value.sources);
    writeJsonLocalStorage(STORAGE_KEY, value);
    this.prefsApi.put(PREFS_KEY, value).subscribe({ error: () => undefined });
  }

  private readLocal(): TimelinePrefsValue {
    return normalizePrefs(readJsonLocalStorage<unknown>(STORAGE_KEY, null));
  }
}
