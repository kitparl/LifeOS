import { Component, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Observable } from 'rxjs';
import { apiErrorMessage } from '../../../core/utils/http';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { ItemPatch, ItineraryEditorComponent, NewItem } from '../components/itinerary-editor.component';
import { PlaceSearchComponent } from '../components/place-search.component';
import { PlaceSheetComponent, PlaceSheetSubmit } from '../components/place-sheet.component';
import { LatLng, MapLine, MapMarker, TravelMapComponent } from '../map/travel-map.component';
import {
  GeoLookup,
  Place,
  ROUTE_MODES,
  RouteLeg,
  RouteMode,
  Stop,
  TRIP_STATUS_LABELS,
  TripDetail,
  dayColor,
  fallbackMessage,
  formatDistance,
  formatDuration,
} from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';
import { decodePolyline } from '../utils/geo';
import { stopDayLabels } from '../utils/itinerary';
import { directionsUrl } from '../utils/google-links';

type MobileTab = 'map' | 'itinerary';

/** One road leg of the current route, labelled with its stops and the day it arrives on. */
interface LegRow {
  from: string;
  to: string;
  dayId: string;
  leg: RouteLeg;
}

/**
 * One trip: map + itinerary side by side on desktop, tabs on mobile (spec §12, §33, §34).
 * Both panes render the same `TripDetail`, so stops, order and route can never disagree.
 * Routes are requested only by the user (spec §13); a stale route offers Recalculate.
 */
@Component({
  selector: 'app-travel-trip-detail',
  standalone: true,
  imports: [FormsModule, RouterLink, TravelMapComponent, ItineraryEditorComponent, PlaceSearchComponent, PlaceSheetComponent],
  template: `
    @if (detail(); as d) {
      <div class="space-y-3">
        <div class="panel space-y-2 text-sm" [style.border-style]="isDraft() ? 'dashed' : null">
          <div class="flex flex-wrap items-center gap-2">
            <input class="input-field min-w-[12rem] flex-1 font-semibold" maxlength="200" aria-label="Trip name" [ngModel]="d.trip.name" (change)="update({ name: val($event) })" />
            <span class="chip text-xs">{{ statusLabels[d.trip.status] }}</span>
            <span class="text-xs" style="color: var(--text-muted)">{{ saveState() }}</span>
          </div>
          <div class="flex flex-wrap items-end gap-2">
            <label class="text-xs">Start
              <input class="input-field" type="date" [ngModel]="d.trip.start_date" (change)="update({ start_date: val($event) || null })" />
            </label>
            <label class="text-xs">End
              <input class="input-field" type="date" [ngModel]="d.trip.end_date" (change)="update({ end_date: val($event) || null })" />
            </label>
            @if (isDraft()) {
              <label class="flex items-center gap-1 text-xs">
                <input type="checkbox" [ngModel]="d.trip.dates_tentative" (ngModelChange)="update({ dates_tentative: $event })" />
                Dates are tentative
              </label>
            }
          </div>
          @if (isDraft()) {
            <p class="text-xs" style="color: var(--text-muted)">
              Draft — changes save automatically. It is not in your Calendar and its places stay in your Travel Wishlist until you confirm the plan.
            </p>
          }
          <div class="flex flex-wrap gap-2">
            @switch (d.trip.status) {
              @case ('draft') {
                <button type="button" class="btn-primary text-xs" [disabled]="busy()" (click)="lifecycle('confirm')">Confirm plan</button>
              }
              @case ('planning') {
                <button type="button" class="btn-secondary text-xs" [disabled]="busy()" (click)="status('booked')">Mark booked</button>
                <button type="button" class="btn-secondary text-xs" [disabled]="busy()" (click)="lifecycle('draft')">Move back to draft</button>
              }
              @case ('booked') {
                <button type="button" class="btn-secondary text-xs" [disabled]="busy()" (click)="status('active')">Start trip</button>
                <button type="button" class="btn-secondary text-xs" [disabled]="busy()" (click)="lifecycle('draft')">Move back to draft</button>
              }
            }
            @if (canComplete()) {
              <button type="button" class="btn-primary text-xs" [disabled]="busy()" (click)="complete()">Complete trip</button>
            }
            <button type="button" class="text-xs" style="color: var(--danger)" [disabled]="busy()" (click)="remove()">Delete trip</button>
            <a routerLink="/travel/trips" class="self-center text-xs underline">All trips</a>
          </div>
          @if (error()) {
            <p class="text-xs" style="color: var(--danger)">{{ error() }}</p>
          }
        </div>

        <div class="flex gap-1 lg:hidden" role="tablist">
          <button type="button" class="text-xs" [class.btn-primary]="tab() === 'map'" [class.btn-secondary]="tab() !== 'map'" (click)="setTab('map')">Map</button>
          <button type="button" class="text-xs" [class.btn-primary]="tab() === 'itinerary'" [class.btn-secondary]="tab() !== 'itinerary'" (click)="setTab('itinerary')">Itinerary</button>
        </div>

        <div class="grid gap-3 lg:grid-cols-2">
          <div class="space-y-2 lg:block" [class.hidden]="tab() !== 'map'">
            @if (d.days.length) {
              <div class="flex flex-wrap gap-1.5" role="group" aria-label="Show day on map">
                <button type="button" class="chip cursor-pointer" [attr.aria-pressed]="!dayFilter()" [style.border-color]="!dayFilter() ? 'var(--primary)' : null" (click)="showDay(null)">All days</button>
                @for (day of d.days; track day.id; let i = $index) {
                  <button
                    type="button"
                    class="chip cursor-pointer"
                    [attr.aria-pressed]="dayFilter() === day.id"
                    [style.border-color]="dayFilter() === day.id ? 'var(--primary)' : null"
                    (click)="showDay(day.id)"
                  >
                    <span [style.color]="'var(' + color(i) + ')'">●</span> Day {{ day.day_index + 1 }}
                  </button>
                }
              </div>
            }
            <app-travel-map #map class="h-[55vh]" [markers]="markers()" [lines]="lines()" [pin]="searchPin()" [fitKey]="fitKey()" [permanentLabels]="showLabels" (markerSelect)="openPlace($event.id)" />
            <div class="panel space-y-2 text-sm">
              <div class="flex flex-wrap items-center gap-2">
                <select class="input-field !w-auto text-xs" aria-label="Travel mode" [(ngModel)]="mode">
                  @for (m of modes; track m.id) {
                    <option [value]="m.id">{{ m.label }}</option>
                  }
                </select>
                <button type="button" class="btn-secondary text-xs" [disabled]="busy() || d.stops.length < 2" (click)="route()">
                  {{ d.route ? 'Recalculate route' : 'Get route' }}
                </button>
                <label class="flex items-center gap-1 text-xs">
                  <input type="checkbox" [(ngModel)]="showLabels" />
                  Show names on map
                </label>
                @if (directions(); as url) {
                  <a class="text-xs underline" [href]="url" target="_blank" rel="noopener noreferrer">Get directions in Google Maps</a>
                }
              </div>
              @if (d.route; as r) {
                <p class="text-xs">
                  {{ distance(r.distance_m) }}
                  @if (duration(r.duration_s); as t) { · {{ t }} }
                  · {{ r.source === 'google' ? 'Google route' : 'straight-line estimate' }} ({{ r.mode }})
                </p>
                @if (r.is_stale) {
                  <p class="text-xs" style="color: var(--warning)">Stops changed — the route may be outdated. Recalculate when ready.</p>
                }
                @if (routeNote(r.fallback_reason); as note) {
                  <p class="text-xs" style="color: var(--text-muted)">{{ note }}</p>
                }
                @if (legRows().length) {
                  <ul class="space-y-1 text-xs" aria-label="Road distance between stops">
                    @for (row of legRows(); track $index) {
                      <li class="flex flex-wrap items-center gap-1">
                        <span [style.color]="'var(' + dayColorOf(row.dayId) + ')'">●</span>
                        <span>{{ row.from }} → {{ row.to }}</span>
                        <span style="color: var(--text-muted)">· {{ distance(row.leg.distance_m) }}@if (duration(row.leg.duration_s); as t) { · {{ t }}}</span>
                      </li>
                    }
                  </ul>
                } @else if (r.source === 'google' && !r.is_stale && !r.legs) {
                  <p class="text-xs" style="color: var(--text-muted)">Recalculate to see the road distance between each stop.</p>
                }
              } @else if (d.stops.length < 2) {
                <p class="text-xs" style="color: var(--text-muted)">Add at least two stops with places to draw a route.</p>
              } @else {
                <p class="text-xs" style="color: var(--text-muted)">Get route to see the road distance between each stop.</p>
              }
            </div>
          </div>

          <div class="space-y-2 lg:block" [class.hidden]="tab() !== 'itinerary'">
            <div class="panel space-y-2 text-sm">
              <div class="flex flex-wrap items-start gap-2">
                <app-place-search class="min-w-[12rem] flex-1" placeholder="Search a new place to add" [bias]="mapCenter" (picked)="pickSearch($event)" />
                <select class="input-field !w-auto text-xs" aria-label="Add places to day" [(ngModel)]="addDayId" (ngModelChange)="addDayChosen = true">
                  <option value="">Not on a day yet</option>
                  @for (day of d.days; track day.id) {
                    <option [value]="day.id">Add to Day {{ day.day_index + 1 }}</option>
                  }
                </select>
              </div>
              <div class="flex flex-wrap items-end gap-2">
                <label class="flex-1 text-xs">Add a saved place
                  <select class="input-field text-xs" [(ngModel)]="placeToAdd" aria-label="Saved place">
                    <option value="">Choose…</option>
                    @for (p of savedPlaces(); track p.id) {
                      <option [value]="p.id">{{ p.name }}</option>
                    }
                  </select>
                </label>
                <button type="button" class="btn-secondary text-xs" [disabled]="!placeToAdd || busy()" (click)="addPlace()">Add to trip</button>
              </div>
            </div>
            <app-itinerary-editor
              [days]="d.days"
              [places]="d.places"
              [canFill]="!!d.trip.start_date && !!d.trip.end_date"
              [disabled]="busy()"
              (reorder)="run(api.reorderItinerary(d.trip.id, $event))"
              (itemPatch)="patchItem($event)"
              (deleteItem)="run(api.deleteItem(d.trip.id, $event))"
              (addItem)="addItem($event)"
              (addDay)="run(api.addDay(d.trip.id))"
              (fillDays)="run(api.fillDays(d.trip.id))"
              (deleteDay)="run(api.deleteDay(d.trip.id, $event))"
              (dayTitle)="run(api.updateDay(d.trip.id, $event.id, { title: $event.title || null }))"
            />
          </div>
        </div>
      </div>
      <app-place-sheet
        [open]="!!searchPin()"
        [point]="searchPin()"
        [lookup]="searchLookup()"
        [busy]="busy()"
        [error]="error()"
        [tripOnly]="true"
        (submitted)="addSearched($event)"
        (closed)="closeSearch()"
      />
    } @else if (notFound()) {
      <p class="text-sm">This trip does not exist. <a routerLink="/travel/trips" class="underline">All trips</a></p>
    } @else {
      <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
    }
  `,
})
export class TripDetailComponent implements OnInit {
  @ViewChild('map') private readonly map?: TravelMapComponent;
  readonly api = inject(TravelApiService);
  private readonly route$ = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly confirm = inject(ConfirmService);

  readonly statusLabels = TRIP_STATUS_LABELS;
  readonly modes = ROUTE_MODES;
  readonly detail = signal<TripDetail | null>(null);
  readonly savedPlaces = signal<Place[]>([]);
  readonly notFound = signal(false);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly saveState = signal('');
  readonly tab = signal<MobileTab>('map');
  readonly selectedDay = signal<string | null>(null);
  private readonly filterClicks = signal(0);
  readonly searchPin = signal<LatLng | null>(null);
  readonly searchLookup = signal<GeoLookup | null>(null);
  readonly mapCenter = (): LatLng | null => this.map?.center() ?? null;
  mode: RouteMode = 'driving';
  showLabels = true;
  placeToAdd = '';
  /** Day that searched and saved places are added to ('' = linked to the trip, not on a day). Defaults to Day 1. */
  addDayId = '';
  addDayChosen = false;

  readonly isDraft = computed(() => this.detail()?.trip.status === 'draft');
  readonly canComplete = computed(() => ['planning', 'booked', 'active'].includes(this.detail()?.trip.status ?? ''));

  /** Selected day on the map (null = all days); falls back to all when that day is removed. */
  readonly dayFilter = computed(() => {
    const id = this.selectedDay();
    return id && this.detail()?.days.some((day) => day.id === id) ? id : null;
  });

  /** Changes on every day-chip click so the map re-fits to what is now shown. */
  readonly fitKey = computed(() => (this.filterClicks() ? `${this.filterClicks()}:${this.dayFilter() ?? 'all'}` : null));

  private readonly dayIndexById = computed(() => new Map((this.detail()?.days ?? []).map((day, i) => [day.id, i])));

  /** Place ids on each day, so a place visited on several days shows under each of them. */
  private readonly placesByDay = computed(() => {
    const byDay = new Map<string, Set<string>>();
    for (const day of this.detail()?.days ?? []) {
      byDay.set(day.id, new Set(day.items.flatMap((item) => (item.place_id ? [item.place_id] : []))));
    }
    return byDay;
  });

  readonly markers = computed<MapMarker[]>(() => {
    const d = this.detail();
    if (!d) return [];
    const day = this.dayFilter();
    const onDay = day ? this.placesByDay().get(day) : null;
    const dayLabels = stopDayLabels(d.days, d.stops);
    const stops: MapMarker[] = d.stops.flatMap((s, i) =>
      onDay && !onDay.has(s.place_id)
        ? []
        : [{ id: s.place_id, kind: 'place', lat: s.lat, lng: s.lng, label: stopLabel(i, s.name, dayLabels.get(i)), color: this.dayColorOf(s.day_id) }],
    );
    if (day) return stops;
    const scheduled = new Set([...this.placesByDay().values()].flatMap((ids) => [...ids]));
    const unscheduled: MapMarker[] = d.places
      .filter((p) => !scheduled.has(p.id))
      .map((p) => ({ id: p.id, kind: 'place', lat: p.lat, lng: p.lng, label: `${p.name} (not on a day yet)`, color: '--text-muted', faded: true }));
    return [...stops, ...unscheduled];
  });

  /** Road legs of the current route, in stop order. Empty when there is no current Google route. */
  private readonly legs = computed<LegRow[]>(() => {
    const d = this.detail();
    const legs = d?.route && !d.route.is_stale ? d.route.legs : null;
    if (!d || !legs || legs.length !== d.stops.length - 1) return [];
    return legs.map((leg, i) => ({ from: d.stops[i].name, to: d.stops[i + 1].name, dayId: d.stops[i + 1].day_id, leg }));
  });

  /** A leg belongs to the day of the stop it arrives at. */
  readonly legRows = computed(() => {
    const day = this.dayFilter();
    return day ? this.legs().filter((row) => row.dayId === day) : this.legs();
  });

  /**
   * Per-day coloured road legs when the route has them; the stored route as one line otherwise;
   * dashed per-day connectors through the stops when there is no current route (no API call).
   */
  readonly lines = computed<MapLine[]>(() => {
    const d = this.detail();
    if (!d) return [];
    const r = d.route;
    const dashed = this.isDraft() || r?.source === 'straight_line';
    if (this.legs().length) {
      return this.legRows().map((row, i) => ({ id: `leg-${i}`, points: decodePolyline(row.leg.polyline), color: this.dayColorOf(row.dayId), dashed }));
    }
    if (r && !r.is_stale && r.polyline) {
      return [{ id: r.id, points: decodePolyline(r.polyline), color: '--primary', dashed }];
    }
    const day = this.dayFilter();
    return connectors(d.stops)
      .filter((c) => !day || c.to.day_id === day)
      .map((c, i) => ({ id: `stop-${i}`, points: [[c.from.lat, c.from.lng], [c.to.lat, c.to.lng]], color: this.dayColorOf(c.to.day_id), dashed: true }));
  });

  readonly directions = computed(() => {
    const d = this.detail();
    return d && d.stops.length ? directionsUrl(d.stops, this.mode) : null;
  });

  ngOnInit(): void {
    const id = this.route$.snapshot.paramMap.get('id') ?? '';
    this.api.getTrip(id).subscribe({
      next: (d) => this.apply(d),
      error: () => this.notFound.set(true),
    });
    this.api.listPlaces({ limit: 100 }).subscribe({ next: (page) => this.savedPlaces.set(page.items) });
  }

  val(event: Event): string {
    return (event.target as HTMLInputElement).value.trim();
  }

  setTab(tab: MobileTab): void {
    this.tab.set(tab);
    if (tab === 'map') setTimeout(() => this.map?.invalidateSize());
  }

  update(patch: Parameters<TravelApiService['updateTrip']>[1]): void {
    const d = this.detail();
    if (!d || patch.name === '') return;
    this.run(this.api.updateTrip(d.trip.id, patch));
  }

  lifecycle(action: 'confirm' | 'draft'): void {
    const d = this.detail();
    if (d) this.run(this.api.tripLifecycle(d.trip.id, action));
  }

  status(status: 'booked' | 'active'): void {
    const d = this.detail();
    if (d) this.run(this.api.setTripStatus(d.trip.id, status));
  }

  async complete(): Promise<void> {
    const d = this.detail();
    if (!d) return;
    const ok = await this.confirm.confirm(
      'Its places become visited. Routes, photos and journal entries all stay.',
      `Complete ${d.trip.name}?`,
      { acceptLabel: 'Complete trip', danger: false },
    );
    if (ok) this.run(this.api.tripLifecycle(d.trip.id, 'complete'));
  }

  async remove(): Promise<void> {
    const d = this.detail();
    if (!d || !(await this.confirm.confirm('Places stay saved; photos and journal entries are kept.', `Delete ${d.trip.name}?`))) return;
    this.api.deleteTrip(d.trip.id).subscribe({ next: () => void this.router.navigate(['/travel/trips']) });
  }

  color(dayIndex: number): string {
    return dayColor(dayIndex);
  }

  dayColorOf(dayId: string): string {
    return dayColor(this.dayIndexById().get(dayId) ?? 0);
  }

  showDay(dayId: string | null): void {
    this.selectedDay.set(dayId);
    this.filterClicks.update((n) => n + 1);
    if (dayId) {
      this.addDayId = dayId;
      this.addDayChosen = true;
    }
  }

  addPlace(): void {
    const d = this.detail();
    if (!d || !this.placeToAdd) return;
    this.run(this.api.addPlaceToTrip(d.trip.id, this.placeToAdd, this.addDayId || null));
    this.placeToAdd = '';
  }

  pickSearch(res: GeoLookup): void {
    if (!res.result) return;
    const point = { lat: res.result.lat, lng: res.result.lng };
    this.error.set(null);
    this.searchLookup.set(res);
    this.searchPin.set(point);
    this.map?.flyTo(point);
  }

  closeSearch(): void {
    this.searchPin.set(null);
    this.searchLookup.set(null);
  }

  /** Save the searched spot as a Place (or reuse the one already saved there), then put it on the chosen day. */
  addSearched(event: PlaceSheetSubmit): void {
    const d = this.detail();
    if (!d) return;
    const dayId = this.addDayId || null;
    this.busy.set(true);
    this.error.set(null);
    this.api.createPlace(event.place).subscribe({
      next: (place) => this.addSearchedToTrip(d.trip.id, place.id, dayId),
      error: (err) => {
        const existing = (err?.error?.detail as { place_id?: string } | undefined)?.place_id;
        if (existing) this.addSearchedToTrip(d.trip.id, existing, dayId);
        else this.fail(err);
      },
    });
  }

  private addSearchedToTrip(tripId: string, placeId: string, dayId: string | null): void {
    this.closeSearch();
    this.run(this.api.addPlaceToTrip(tripId, placeId, dayId));
  }

  addItem(item: NewItem): void {
    const d = this.detail();
    if (d) this.run(this.api.addItem(d.trip.id, item));
  }

  patchItem(event: ItemPatch): void {
    const d = this.detail();
    if (d) this.run(this.api.updateItem(d.trip.id, event.id, event.patch));
  }

  route(): void {
    const d = this.detail();
    if (!d) return;
    this.busy.set(true);
    this.api.computeRoute(d.trip.id, this.mode).subscribe({
      next: (r) => {
        this.busy.set(false);
        this.detail.set({ ...d, route: { ...r, is_stale: false } });
      },
      error: (err) => this.fail(err),
    });
  }

  openPlace(id: string): void {
    void this.router.navigate(['/travel/places', id]);
  }

  distance(m: number): string {
    return formatDistance(m);
  }

  duration(s: number | null): string | null {
    return formatDuration(s);
  }

  routeNote(reason: string | null): string | null {
    if (!reason) return null;
    if (reason === 'transit_multi_stop') return 'Google transit routing supports only two stops, so this is a straight-line estimate.';
    return fallbackMessage(reason)?.replace('Coordinates are saved; type a name.', 'Showing a straight-line estimate.') ?? null;
  }

  /** Every edit returns the full trip, so map and itinerary re-render from one source of truth. */
  run(request: Observable<TripDetail>): void {
    this.busy.set(true);
    this.error.set(null);
    this.saveState.set('Saving…');
    request.subscribe({
      next: (d) => {
        this.apply(d);
        this.busy.set(false);
        this.saveState.set('All changes saved');
      },
      error: (err) => this.fail(err),
    });
  }

  private apply(d: TripDetail): void {
    this.detail.set(d);
    if (d.route) this.mode = d.route.mode;
    if (!this.addDayChosen || !d.days.some((day) => day.id === this.addDayId)) this.addDayId = d.days[0]?.id ?? '';
  }

  private fail(err: unknown): void {
    this.busy.set(false);
    this.saveState.set('');
    this.error.set(apiErrorMessage(err, 'Could not save that change'));
  }
}

/** "3. Tosh" or, for a day's first/last stop, "3. Tosh · Day 2 end". */
function stopLabel(index: number, name: string, dayLabels: string[] | undefined): string {
  const base = `${index + 1}. ${name}`;
  return dayLabels?.length ? `${base} · ${dayLabels.join(' · ')}` : base;
}

/** Consecutive stop pairs (the dashed preview drawn before a route exists). */
function connectors(stops: readonly Stop[]): { from: Stop; to: Stop }[] {
  return stops.slice(1).map((to, i) => ({ from: stops[i], to }));
}
