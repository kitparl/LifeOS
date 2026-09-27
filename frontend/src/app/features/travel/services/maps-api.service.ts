import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, debounceTime, distinctUntilChanged, map, of, switchMap } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { GeoLookup, MapsStatus, Suggestions } from '../models/travel.models';

export const SEARCH_DEBOUNCE_MS = 300;
export const SEARCH_MIN_LENGTH = 3;

/**
 * Map lookups through the backend proxy (every call is usage-tracked and cost-protected server-side).
 * The browser never calls Google directly.
 */
@Injectable({ providedIn: 'root' })
export class MapsApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/travel/maps`;
  private session = newSessionToken();

  status(): Observable<MapsStatus> {
    return this.http.get<MapsStatus>(`${this.base}/status`);
  }

  reverseGeocode(lat: number, lng: number): Observable<GeoLookup> {
    return this.http.post<GeoLookup>(`${this.base}/reverse-geocode`, { lat, lng });
  }

  /**
   * Debounced, min-length, cancelling search (spec §31). Short queries never reach the server;
   * `switchMap` drops the in-flight request when the user keeps typing.
   */
  searchSuggestions(query$: Observable<string>, bias?: () => { lat: number; lng: number } | null): Observable<Suggestions> {
    return query$.pipe(
      map((q) => q.trim()),
      debounceTime(SEARCH_DEBOUNCE_MS),
      distinctUntilChanged(),
      switchMap((q) => {
        if (q.length < SEARCH_MIN_LENGTH) return of<Suggestions>({ suggestions: [], fallback_reason: null });
        let params = new HttpParams().set('q', q).set('session', this.session);
        const center = bias?.();
        if (center) params = params.set('lat', center.lat.toFixed(5)).set('lng', center.lng.toFixed(5));
        return this.http.get<Suggestions>(`${this.base}/autocomplete`, { params });
      }),
    );
  }

  /** Selecting a suggestion ends the Places session (Google's session pattern); the next search starts a new one. */
  placeDetails(externalPlaceId: string): Observable<GeoLookup> {
    const params = new HttpParams().set('session', this.session);
    this.session = newSessionToken();
    return this.http.get<GeoLookup>(`${this.base}/place/${encodeURIComponent(externalPlaceId)}`, { params });
  }
}

function newSessionToken(): string {
  return crypto.randomUUID();
}
