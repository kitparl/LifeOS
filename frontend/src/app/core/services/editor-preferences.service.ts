import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { environment } from '../../../environments/environment';

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
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/preferences`;

  private readonly prefs = signal<EditorPrefsValue>({ ...DEFAULT_PREFS });

  readonly keymap = signal<EditorKeymap>('default');

  init(): void {
    const local = this.readLocal();
    this.applyPrefs(local);

    this.http.get<{ key: string; value: EditorPrefsValue | null }>(`${this.api}/${PREFS_KEY}`).subscribe({
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
    const normalized = normalizePrefs(value);
    this.prefs.set(normalized);
    this.keymap.set(normalized.keymap);
  }

  private commit(value: EditorPrefsValue): void {
    const normalized = normalizePrefs(value);
    this.applyPrefs(normalized);
    this.cacheLocal(normalized);
    this.saveToApi(normalized);
  }

  private saveToApi(value: EditorPrefsValue): void {
    this.http.put(`${this.api}/${PREFS_KEY}`, { value }).subscribe({ error: () => undefined });
  }

  private cacheLocal(value: EditorPrefsValue): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    } catch {
      /* ignore */
    }
  }

  private readLocal(): EditorPrefsValue {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { ...DEFAULT_PREFS };
      return normalizePrefs(JSON.parse(raw));
    } catch {
      return { ...DEFAULT_PREFS };
    }
  }
}
