import { InjectionToken } from '@angular/core';

/**
 * Who is using News. Logged-in users get the full module ('user'). The public Explore Tools mount
 * provides 'guest': live news is browsable, but saving and collections (account data) are locked.
 */
export type NewsAccessMode = 'user' | 'guest';

export const NEWS_ACCESS_MODE = new InjectionToken<NewsAccessMode>('NEWS_ACCESS_MODE', {
  providedIn: 'root',
  factory: () => 'user',
});

/** Absolute root of the News routes for a mode (for components rendered at more than one route depth). */
export function newsRootPath(mode: NewsAccessMode): string {
  return mode === 'guest' ? '/explore/news' : '/news';
}
