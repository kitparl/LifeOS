/** Harmless UI preferences only (never user data). Storage can be unavailable, so every access is guarded. */

export const NEWS_COUNTRY_KEY = 'lifeos-news-country';
export const NEWS_CATEGORY_KEY = 'lifeos-news-category';

export function readNewsPref(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function writeNewsPref(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Preference is simply not remembered.
  }
}
