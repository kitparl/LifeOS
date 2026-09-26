import { Injectable, computed, inject, signal } from '@angular/core';
import {
  readJsonLocalStorage,
  writeJsonLocalStorage,
} from './preferences-sync';
import { PreferencesApiService } from './preferences-api.service';

export type NewsLayout = 'list' | 'grid' | 'cards';

export const NEWS_LAYOUT_OPTIONS: readonly { value: NewsLayout; label: string }[] = [
  { value: 'list', label: 'List' },
  { value: 'grid', label: 'Grid' },
  { value: 'cards', label: 'Cards' },
];

/** `'latest'` opens the Latest tab; any other value is a category id opened on the Categories tab. */
export const NEWS_DEFAULT_VIEW_LATEST = 'latest';

export interface NewsPrefsValue {
  layout: NewsLayout;
  defaultView: string;
}

const STORAGE_KEY = 'lifeos-news-prefs';
const PREFS_KEY = 'news';
const MAX_VIEW_LENGTH = 64;
const DEFAULT_PREFS: NewsPrefsValue = { layout: 'cards', defaultView: NEWS_DEFAULT_VIEW_LATEST };

function normalizeLayout(value: unknown): NewsLayout {
  return NEWS_LAYOUT_OPTIONS.some((o) => o.value === value) ? (value as NewsLayout) : DEFAULT_PREFS.layout;
}

/** Category ids are checked against the live list where they are used (unknown ids fall back there). */
function normalizeDefaultView(value: unknown): string {
  return typeof value === 'string' && value && value.length <= MAX_VIEW_LENGTH ? value : DEFAULT_PREFS.defaultView;
}

function normalizePrefs(raw: unknown): NewsPrefsValue {
  if (raw && typeof raw === 'object') {
    const value = raw as Partial<NewsPrefsValue>;
    return { layout: normalizeLayout(value.layout), defaultView: normalizeDefaultView(value.defaultView) };
  }
  return { ...DEFAULT_PREFS };
}

@Injectable({ providedIn: 'root' })
export class NewsPreferencesService {
  private readonly prefsApi = inject(PreferencesApiService);

  /** Seed from localStorage immediately so News opens on the right view before init() resolves. */
  private readonly prefs = signal<NewsPrefsValue>(this.readLocal());

  readonly layout = computed(() => this.prefs().layout);
  readonly defaultView = computed(() => this.prefs().defaultView);
  /** The default category, or `null` when News should open on Latest. */
  readonly defaultCategory = computed(() =>
    this.defaultView() === NEWS_DEFAULT_VIEW_LATEST ? null : this.defaultView(),
  );

  init(): void {
    this.applyPrefs(this.readLocal());

    this.prefsApi.get<NewsPrefsValue>(PREFS_KEY).subscribe({
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

  setLayout(layout: NewsLayout): void {
    this.commit({ ...this.prefs(), layout });
  }

  setDefaultView(defaultView: string): void {
    this.commit({ ...this.prefs(), defaultView });
  }

  private applyPrefs(value: NewsPrefsValue): void {
    this.prefs.set(normalizePrefs(value));
  }

  private commit(value: NewsPrefsValue): void {
    const normalized = normalizePrefs(value);
    this.applyPrefs(normalized);
    this.cacheLocal(normalized);
    this.saveToApi(normalized);
  }

  private saveToApi(value: NewsPrefsValue): void {
    this.prefsApi.put(PREFS_KEY, value).subscribe({ error: () => undefined });
  }

  private cacheLocal(value: NewsPrefsValue): void {
    writeJsonLocalStorage(STORAGE_KEY, value);
  }

  private readLocal(): NewsPrefsValue {
    return normalizePrefs(readJsonLocalStorage<unknown>(STORAGE_KEY, DEFAULT_PREFS));
  }
}
