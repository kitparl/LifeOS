import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Page, toPage } from '../../../core/utils/http';
import {
  Adventure,
  AdventureDetail,
  AdventureUpdate,
  AdventureWaypoint,
  GpxPreview,
  ItemUpdate,
  JournalEntry,
  JournalInput,
  Marker,
  Place,
  PlaceCreate,
  PlaceHistory,
  PlaceStatus,
  PhotoMeta,
  PlaceUpdate,
  Route,
  RouteDetail,
  RouteMode,
  TripCreate,
  TripDetail,
  TripListItem,
  TripStatus,
  TravelPhoto,
  TripUpdate,
  WorldOverview,
} from '../models/travel.models';

export interface PlaceListQuery {
  status?: PlaceStatus;
  category?: string;
  tag?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

/** Travel CRUD. Map lookups (which may cost money) live in `MapsApiService`. */
@Injectable({ providedIn: 'root' })
export class TravelApiService {
  private readonly http = inject(HttpClient);
  readonly base = `${environment.apiUrl}/travel`;

  listPlaces(query: PlaceListQuery = {}): Observable<Page<Place>> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') params = params.set(key, String(value));
    }
    return this.http.get<Place[]>(`${this.base}/places`, { params, observe: 'response' }).pipe(map(toPage));
  }

  getPlace(id: string): Observable<Place> {
    return this.http.get<Place>(`${this.base}/places/${id}`);
  }

  createPlace(body: PlaceCreate): Observable<Place> {
    return this.http.post<Place>(`${this.base}/places`, body);
  }

  updatePlace(id: string, body: PlaceUpdate): Observable<Place> {
    return this.http.patch<Place>(`${this.base}/places/${id}`, body);
  }

  deletePlace(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/places/${id}`);
  }

  setTags(id: string, names: string[]): Observable<Place> {
    return this.http.put<Place>(`${this.base}/places/${id}/tags`, { names });
  }

  listTags(): Observable<string[]> {
    return this.http.get<string[]>(`${this.base}/tags`);
  }

  placeHistory(id: string): Observable<PlaceHistory> {
    return this.http.get<PlaceHistory>(`${this.base}/places/${id}/history`);
  }

  markers(): Observable<Marker[]> {
    return this.http.get<Marker[]>(`${this.base}/markers`);
  }

  // ---- trips ------------------------------------------------------------------------------------

  listTrips(query: { status?: TripStatus; limit?: number; offset?: number } = {}): Observable<Page<TripListItem>> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) params = params.set(key, String(value));
    }
    return this.http.get<TripListItem[]>(`${this.base}/trips`, { params, observe: 'response' }).pipe(map(toPage));
  }

  createTrip(body: TripCreate): Observable<TripDetail> {
    return this.http.post<TripDetail>(`${this.base}/trips`, body);
  }

  getTrip(id: string): Observable<TripDetail> {
    return this.http.get<TripDetail>(`${this.base}/trips/${id}`);
  }

  updateTrip(id: string, body: TripUpdate): Observable<TripDetail> {
    return this.http.patch<TripDetail>(`${this.base}/trips/${id}`, body);
  }

  deleteTrip(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/trips/${id}`);
  }

  /** confirm | draft | complete */
  tripLifecycle(id: string, action: 'confirm' | 'draft' | 'complete'): Observable<TripDetail> {
    return this.http.post<TripDetail>(`${this.base}/trips/${id}/${action}`, {});
  }

  setTripStatus(id: string, status: 'planning' | 'booked' | 'active'): Observable<TripDetail> {
    return this.http.post<TripDetail>(`${this.base}/trips/${id}/status`, { status });
  }

  addPlaceToTrip(tripId: string, placeId: string, dayId?: string | null): Observable<TripDetail> {
    return this.http.post<TripDetail>(`${this.base}/trips/${tripId}/places/${placeId}`, { day_id: dayId ?? null });
  }

  removePlaceFromTrip(tripId: string, placeId: string): Observable<TripDetail> {
    return this.http.delete<TripDetail>(`${this.base}/trips/${tripId}/places/${placeId}`);
  }

  addDay(tripId: string): Observable<TripDetail> {
    return this.http.post<TripDetail>(`${this.base}/trips/${tripId}/days`, {});
  }

  fillDays(tripId: string): Observable<TripDetail> {
    return this.http.post<TripDetail>(`${this.base}/trips/${tripId}/days/fill`, {});
  }

  updateDay(tripId: string, dayId: string, body: { title?: string | null; notes?: string | null }): Observable<TripDetail> {
    return this.http.patch<TripDetail>(`${this.base}/trips/${tripId}/days/${dayId}`, body);
  }

  deleteDay(tripId: string, dayId: string): Observable<TripDetail> {
    return this.http.delete<TripDetail>(`${this.base}/trips/${tripId}/days/${dayId}`);
  }

  addItem(tripId: string, body: { day_id: string; title: string; place_id?: string | null }): Observable<TripDetail> {
    return this.http.post<TripDetail>(`${this.base}/trips/${tripId}/items`, body);
  }

  updateItem(tripId: string, itemId: string, body: ItemUpdate): Observable<TripDetail> {
    return this.http.patch<TripDetail>(`${this.base}/trips/${tripId}/items/${itemId}`, body);
  }

  deleteItem(tripId: string, itemId: string): Observable<TripDetail> {
    return this.http.delete<TripDetail>(`${this.base}/trips/${tripId}/items/${itemId}`);
  }

  /** The whole layout after one drag: `{day_id: [item_id, ...]}`. */
  reorderItinerary(tripId: string, days: Record<string, string[]>): Observable<TripDetail> {
    return this.http.put<TripDetail>(`${this.base}/trips/${tripId}/itinerary/order`, { days });
  }

  computeRoute(tripId: string, mode: RouteMode): Observable<Route> {
    return this.http.post<Route>(`${this.base}/trips/${tripId}/route`, { mode });
  }

  // ---- adventures, routes, GPX -------------------------------------------------------------------

  listAdventures(query: { trip_id?: string; limit?: number } = {}): Observable<Page<Adventure>> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) params = params.set(key, String(value));
    }
    return this.http.get<Adventure[]>(`${this.base}/adventures`, { params, observe: 'response' }).pipe(map(toPage));
  }

  createAdventure(body: { name: string; kind: string; trip_id?: string | null }): Observable<AdventureDetail> {
    return this.http.post<AdventureDetail>(`${this.base}/adventures`, body);
  }

  getAdventure(id: string): Observable<AdventureDetail> {
    return this.http.get<AdventureDetail>(`${this.base}/adventures/${id}`);
  }

  updateAdventure(id: string, body: AdventureUpdate): Observable<AdventureDetail> {
    return this.http.patch<AdventureDetail>(`${this.base}/adventures/${id}`, body);
  }

  deleteAdventure(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/adventures/${id}`);
  }

  setWaypoints(id: string, waypoints: AdventureWaypoint[]): Observable<AdventureDetail> {
    const body = waypoints.map(({ lat, lng, name, kind, elevation_m }) => ({ lat, lng, name, kind, elevation_m }));
    return this.http.put<AdventureDetail>(`${this.base}/adventures/${id}/waypoints`, { waypoints: body });
  }

  saveDrawnRoute(body: {
    name: string;
    mode: RouteMode;
    points: [number, number][];
    adventure_id?: string | null;
    trip_id?: string | null;
  }): Observable<RouteDetail> {
    return this.http.post<RouteDetail>(`${this.base}/routes`, body);
  }

  fillElevation(routeId: string): Observable<RouteDetail> {
    return this.http.post<RouteDetail>(`${this.base}/routes/${routeId}/elevation`, {});
  }

  /** Downloaded through HttpClient so the auth header is sent (a plain link would not carry it). */
  exportGpx(routeId: string): Observable<Blob> {
    return this.http.get(`${this.base}/routes/${routeId}/gpx`, { responseType: 'blob' });
  }

  previewGpx(file: File): Observable<GpxPreview> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<GpxPreview>(`${this.base}/gpx/preview`, form);
  }

  importGpx(file: File, name: string, links: { adventure_id?: string | null; trip_id?: string | null }): Observable<RouteDetail> {
    const form = new FormData();
    form.append('file', file);
    form.append('name', name);
    if (links.adventure_id) form.append('adventure_id', links.adventure_id);
    if (links.trip_id) form.append('trip_id', links.trip_id);
    return this.http.post<RouteDetail>(`${this.base}/gpx`, form);
  }

  // ---- memories + world --------------------------------------------------------------------------

  listPhotos(query: { trip_id?: string; place_id?: string; adventure_id?: string; journal_entry_id?: string; limit?: number; offset?: number } = {}): Observable<Page<TravelPhoto>> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') params = params.set(key, String(value));
    }
    return this.http.get<TravelPhoto[]>(`${this.base}/photos`, { params, observe: 'response' }).pipe(map(toPage));
  }

  uploadPhoto(file: File, meta: PhotoMeta): Observable<TravelPhoto> {
    const form = new FormData();
    form.append('file', file);
    for (const [key, value] of Object.entries(meta)) {
      if (value !== undefined && value !== null && value !== '') form.append(key, String(value));
    }
    return this.http.post<TravelPhoto>(`${this.base}/photos`, form);
  }

  updatePhoto(id: string, body: Partial<Pick<TravelPhoto, 'lat' | 'lng' | 'caption' | 'place_id' | 'trip_id'>>): Observable<TravelPhoto> {
    return this.http.patch<TravelPhoto>(`${this.base}/photos/${id}`, body);
  }

  deletePhoto(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/photos/${id}`);
  }

  listJournal(query: { trip_id?: string; place_id?: string; limit?: number } = {}): Observable<Page<JournalEntry>> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') params = params.set(key, String(value));
    }
    return this.http.get<JournalEntry[]>(`${this.base}/journal`, { params, observe: 'response' }).pipe(map(toPage));
  }

  createJournal(body: JournalInput): Observable<JournalEntry> {
    return this.http.post<JournalEntry>(`${this.base}/journal`, body);
  }

  updateJournal(id: string, body: Partial<JournalInput>): Observable<JournalEntry> {
    return this.http.patch<JournalEntry>(`${this.base}/journal/${id}`, body);
  }

  deleteJournal(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/journal/${id}`);
  }

  world(): Observable<WorldOverview> {
    return this.http.get<WorldOverview>(`${this.base}/world`);
  }
}
