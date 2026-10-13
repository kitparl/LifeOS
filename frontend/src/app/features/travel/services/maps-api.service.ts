import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { GeoLookup, MapsStatus, Suggestions } from '../models/travel.models';
import { LatLngBias, newSessionToken, suggestionStream } from '../utils/place-suggestions';

export { SEARCH_DEBOUNCE_MS, SEARCH_MIN_LENGTH } from '../utils/place-suggestions';

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

  /** Debounced, min-length, cancelling search (see `suggestionStream`). */
  searchSuggestions(query$: Observable<string>, bias?: () => LatLngBias): Observable<Suggestions> {
    return suggestionStream(query$, (q, center) => this.autocomplete(q, center), bias);
  }

  private autocomplete(q: string, center: LatLngBias): Observable<Suggestions> {
    let params = new HttpParams().set('q', q).set('session', this.session);
    if (center) params = params.set('lat', center.lat.toFixed(5)).set('lng', center.lng.toFixed(5));
    return this.http.get<Suggestions>(`${this.base}/autocomplete`, { params });
  }

  /** Selecting a suggestion ends the Places session (Google's session pattern); the next search starts a new one. */
  placeDetails(externalPlaceId: string): Observable<GeoLookup> {
    const params = new HttpParams().set('session', this.session);
    this.session = newSessionToken();
    return this.http.get<GeoLookup>(`${this.base}/place/${encodeURIComponent(externalPlaceId)}`, { params });
  }
}
