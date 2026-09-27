import { Component, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Observable } from 'rxjs';
import { apiErrorMessage } from '../../../core/utils/http';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { ItemPatch, ItineraryEditorComponent, NewItem } from '../components/itinerary-editor.component';
import { MapLine, MapMarker, TravelMapComponent } from '../map/travel-map.component';
import {
  PLACE_STATUS_COLORS,
  Place,
  ROUTE_MODES,
  RouteMode,
  TRIP_STATUS_LABELS,
  TripDetail,
  fallbackMessage,
  formatDistance,
  formatDuration,
} from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';
import { decodePolyline } from '../utils/geo';
import { directionsUrl } from '../utils/google-links';

type MobileTab = 'map' | 'itinerary';

/**
 * One trip: map + itinerary side by side on desktop, tabs on mobile (spec §12, §33, §34).
 * Both panes render the same `TripDetail`, so stops, order and route can never disagree.
 * Routes are requested only by the user (spec §13); a stale route offers Recalculate.
 */
@Component({
  selector: 'app-travel-trip-detail',
  standalone: true,
  imports: [FormsModule, RouterLink, TravelMapComponent, ItineraryEditorComponent],
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
            <app-travel-map #map class="h-[55vh]" [markers]="markers()" [lines]="lines()" (markerSelect)="openPlace($event.id)" />
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
              } @else if (d.stops.length < 2) {
                <p class="text-xs" style="color: var(--text-muted)">Add at least two stops with places to draw a route.</p>
              }
            </div>
          </div>

          <div class="space-y-2 lg:block" [class.hidden]="tab() !== 'itinerary'">
            <div class="panel flex flex-wrap items-end gap-2 text-sm">
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
  mode: RouteMode = 'driving';
  placeToAdd = '';

  readonly isDraft = computed(() => this.detail()?.trip.status === 'draft');
  readonly canComplete = computed(() => ['planning', 'booked', 'active'].includes(this.detail()?.trip.status ?? ''));

  readonly markers = computed<MapMarker[]>(() => {
    const d = this.detail();
    if (!d) return [];
    const statusById = new Map(d.places.map((p) => [p.id, p.status]));
    return d.stops.map((s, i) => ({
      id: s.place_id,
      kind: 'place',
      lat: s.lat,
      lng: s.lng,
      label: `${i + 1}. ${s.name}`,
      color: PLACE_STATUS_COLORS[statusById.get(s.place_id) ?? 'wishlist'],
    }));
  });

  /** The stored route when current; otherwise a dashed connector through the stops (no API call). */
  readonly lines = computed<MapLine[]>(() => {
    const d = this.detail();
    if (!d) return [];
    const r = d.route;
    if (r && !r.is_stale && r.polyline) {
      return [{ id: r.id, points: decodePolyline(r.polyline), color: '--primary', dashed: this.isDraft() || r.source === 'straight_line' }];
    }
    return [{ id: 'stops', points: d.stops.map((s) => [s.lat, s.lng] as [number, number]), color: '--text-muted', dashed: true }];
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

  addPlace(): void {
    const d = this.detail();
    if (!d || !this.placeToAdd) return;
    const firstDay = d.days[0]?.id ?? null;
    this.run(this.api.addPlaceToTrip(d.trip.id, this.placeToAdd, firstDay));
    this.placeToAdd = '';
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
  }

  private fail(err: unknown): void {
    this.busy.set(false);
    this.saveState.set('');
    this.error.set(apiErrorMessage(err, 'Could not save that change'));
  }
}
