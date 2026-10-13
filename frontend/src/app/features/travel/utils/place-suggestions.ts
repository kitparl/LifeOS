import { Observable, debounceTime, distinctUntilChanged, map, of, switchMap } from 'rxjs';
import { Suggestions } from '../models/travel.models';

export const SEARCH_DEBOUNCE_MS = 300;
export const SEARCH_MIN_LENGTH = 3;

export type LatLngBias = { lat: number; lng: number } | null;

/**
 * Debounced, min-length, cancelling place search (spec §31), whatever backend endpoint serves it:
 * short queries never reach the server and `switchMap` drops the in-flight request while typing.
 * Used by the LifeOS place search and by the shared trip planner.
 */
export function suggestionStream(
  query$: Observable<string>,
  fetch: (query: string, bias: LatLngBias) => Observable<Suggestions>,
  bias?: () => LatLngBias,
): Observable<Suggestions> {
  return query$.pipe(
    map((q) => q.trim()),
    debounceTime(SEARCH_DEBOUNCE_MS),
    distinctUntilChanged(),
    switchMap((q) => {
      if (q.length < SEARCH_MIN_LENGTH) return of<Suggestions>({ suggestions: [], fallback_reason: null });
      return fetch(q, bias?.() ?? null);
    }),
  );
}

/** A Places session groups a search with the pick that ends it (Google bills them together). */
export function newSessionToken(): string {
  return crypto.randomUUID();
}
