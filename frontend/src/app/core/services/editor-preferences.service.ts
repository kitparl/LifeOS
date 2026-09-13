import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import {
  PreferencesApi,
  readJsonLocalStorage,
  writeJsonLocalStorage,
} from './preferences-sync';

export type EditorKeymap = 'default' | 'vim';

export interface EditorPrefsValue {
  keymap: EditorKeymap;
}

const STORAGE_KEY = 'lifeos-editor-prefs';
const PREFS_KEY = 'editor';
const DEFAULT_PREFS: EditorPrefsValue = { keymap: 'default' };

function normalizeKeymap(value: unknown): EditorKeymap {
  return value === 'vim' ? 'vim' : 'default';
}

function normalizePrefs(raw: unknown): EditorPrefsValue {
  if (raw && typeof raw === 'object' && 'keymap' in raw) {
    return { keymap: normalizeKeymap((raw as EditorPrefsValue).keymap) };
  }
  return { ...DEFAULT_PREFS };
}

@Injectable({ providedIn: 'root' })
export class EditorPreferencesService {
  private readonly prefsApi = new PreferencesApi(inject(HttpClient));

  private readonly prefs = signal<EditorPrefsValue>({ ...DEFAULT_PREFS });

  readonly keymap = computed(() => this.prefs().keymap);

  init(): void {
    const local = this.readLocal();
    this.applyPrefs(local);

    this.prefsApi.get<EditorPrefsValue>(PREFS_KEY).subscribe({
      next: (resp) => {
        if (resp.value && typeof resp.value === 'object') {
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

  setKeymap(keymap: EditorKeymap): void {
    this.commit({ keymap: normalizeKeymap(keymap) });
  }

  private applyPrefs(value: EditorPrefsValue): void {
    this.prefs.set(normalizePrefs(value));
  }

  private commit(value: EditorPrefsValue): void {
    const normalized = normalizePrefs(value);
    this.applyPrefs(normalized);
    this.cacheLocal(normalized);
    this.saveToApi(normalized);
  }

  private saveToApi(value: EditorPrefsValue): void {
    this.prefsApi.put(PREFS_KEY, value).subscribe({ error: () => undefined });
  }

  private cacheLocal(value: EditorPrefsValue): void {
    writeJsonLocalStorage(STORAGE_KEY, value);
  }

  private readLocal(): EditorPrefsValue {
    return normalizePrefs(readJsonLocalStorage<unknown>(STORAGE_KEY, DEFAULT_PREFS));
  }
}
