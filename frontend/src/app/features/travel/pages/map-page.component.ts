import { Component, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { apiErrorMessage } from '../../../core/utils/http';
import { PlaceSearchComponent } from '../components/place-search.component';
import { PlaceSheetComponent, PlaceSheetSubmit } from '../components/place-sheet.component';
import { TripPickerComponent } from '../components/trip-picker.component';
import { LatLng, MapMarker, TravelMapComponent } from '../map/travel-map.component';
import {
  GeoLookup,
  MAP_LAYERS,
  MapLayer,
  Marker,
  TripDetail,
  markerColor,
  markerLayer,
} from '../models/travel.models';
import { MapsApiService } from '../services/maps-api.service';
import { TravelApiService } from '../services/travel-api.service';

/**
 * Map-first Explore (spec §5/§6, milestone §38): tap anywhere → pin → reverse geocode → sheet → save.
 * Search and tap produce the same Place (spec §7). Only taps, searches and saves call the API.
 */
@Component({
  selector: 'app-travel-map-page',
  standalone: true,
  imports: [RouterLink, TravelMapComponent, PlaceSearchComponent, PlaceSheetComponent, TripPickerComponent],
  template: `
    <div class="space-y-2">
      <div class="flex flex-wrap items-start gap-2">
        <app-place-search
          class="min-w-[14rem] flex-1"
          placeholder="Search places (or just tap the map)"
          [bias]="mapCenter"
          (picked)="pick($event)"
        />
      </div>

      <div class="flex flex-wrap gap-1.5" role="group" aria-label="Map layers">
        @for (l of layers; track l.id) {
          <button
            type="button"
            class="chip cursor-pointer"
            [attr.aria-pressed]="visible().has(l.id)"
            [style.background]="visible().has(l.id) ? 'var(--primary-soft)' : null"
            [style.border-color]="visible().has(l.id) ? 'var(--primary)' : null"
            (click)="toggleLayer(l.id)"
          >
            {{ visible().has(l.id) ? '☑' : '☐' }} {{ l.label }}
          </button>
        }
      </div>

      @if (message(); as m) {
        <p class="text-xs" style="color: var(--success)">
          {{ m.text }}
          @if (m.placeId) {
            <a class="underline" [routerLink]="['/travel/places', m.placeId]">Open place</a>
          }
        </p>
      }

      <app-travel-map
        #map
        class="h-[65vh]"
        [markers]="mapMarkers()"
        [pin]="pin()"
        [toolActive]="true"
        ariaLabel="Travel map. Tap anywhere to drop a pin."
        (mapTap)="onTap($event)"
        (markerSelect)="onMarker($event)"
      />
      <p class="text-xs" style="color: var(--text-muted)">Tap or long-press anywhere to drop a pin and save it.</p>

      <app-place-sheet
        [open]="sheetOpen()"
        [point]="pin()"
        [lookup]="lookup()"
        [loading]="lookingUp()"
        [busy]="saving()"
        [error]="error()"
        [allowTrip]="true"
        (submitted)="save($event)"
        (closed)="closeSheet()"
      />
      <app-trip-picker
        [open]="!!tripPick()"
        [placeId]="tripPick()?.id ?? null"
        [placeName]="tripPick()?.name ?? ''"
        (added)="addedToTrip($event)"
        (closed)="tripPick.set(null)"
      />
    </div>
  `,
})
export class MapPageComponent implements OnInit {
  @ViewChild('map') private readonly map?: TravelMapComponent;
  private readonly api = inject(TravelApiService);
  private readonly maps = inject(MapsApiService);
  private readonly router = inject(Router);

  readonly layers = MAP_LAYERS;
  readonly markers = signal<Marker[]>([]);
  readonly visible = signal<ReadonlySet<MapLayer>>(new Set(MAP_LAYERS.map((l) => l.id)));
  readonly pin = signal<LatLng | null>(null);
  readonly lookup = signal<GeoLookup | null>(null);
  readonly lookingUp = signal(false);
  readonly sheetOpen = signal(false);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly message = signal<{ text: string; placeId?: string } | null>(null);
  readonly tripPick = signal<{ id: string; name: string } | null>(null);
  readonly mapCenter = (): LatLng | null => this.map?.center() ?? null;

  readonly mapMarkers = computed<MapMarker[]>(() =>
    this.markers()
      .filter((m) => this.visible().has(markerLayer(m)))
      .map((m) => ({ id: m.id, kind: m.kind, lat: m.lat, lng: m.lng, label: m.label, color: markerColor(m) })),
  );

  ngOnInit(): void {
    this.loadMarkers();
  }

  toggleLayer(id: MapLayer): void {
    const next = new Set(this.visible());
    if (next.has(id)) next.delete(id);
    else next.add(id);
    this.visible.set(next);
  }

  onTap(point: LatLng): void {
    this.pin.set(point);
    this.lookup.set(null);
    this.error.set(null);
    this.sheetOpen.set(true);
    this.lookingUp.set(true);
    this.maps.reverseGeocode(point.lat, point.lng).subscribe({
      next: (res) => this.finishLookup(res),
      error: () => this.finishLookup({ result: null, fallback_reason: 'provider_unavailable' }),
    });
  }

  pick(res: GeoLookup): void {
    if (!res.result) return;
    const point = { lat: res.result.lat, lng: res.result.lng };
    this.map?.flyTo(point);
    this.pin.set(point);
    this.error.set(null);
    this.finishLookup(res);
    this.sheetOpen.set(true);
  }

  onMarker(marker: MapMarker): void {
    const routes: Record<string, string> = {
      place: '/travel/places',
      trip: '/travel/trips',
      adventure: '/travel/adventures',
    };
    if (marker.kind === 'photo') void this.router.navigate(['/travel/memories']);
    else if (routes[marker.kind]) void this.router.navigate([routes[marker.kind], marker.id]);
  }

  save(event: PlaceSheetSubmit): void {
    this.saving.set(true);
    this.error.set(null);
    this.api.createPlace(event.place).subscribe({
      next: (place) => {
        this.saving.set(false);
        this.closeSheet();
        this.message.set({
          text: event.intent === 'wishlist' ? `${place.name} added to your Travel Wishlist.` : `${place.name} saved.`,
          placeId: place.id,
        });
        this.loadMarkers();
        if (event.intent === 'trip') this.tripPick.set({ id: place.id, name: place.name });
      },
      error: (err) => {
        this.saving.set(false);
        const existing = (err?.error?.detail as { place_id?: string } | undefined)?.place_id;
        if (existing) {
          this.closeSheet();
          this.message.set({ text: 'This spot is already saved.', placeId: existing });
          if (event.intent === 'trip') this.tripPick.set({ id: existing, name: event.place.name });
          return;
        }
        this.error.set(apiErrorMessage(err, 'Could not save this place'));
      },
    });
  }

  addedToTrip(detail: TripDetail): void {
    this.tripPick.set(null);
    this.message.set({ text: `Added to ${detail.trip.name}.` });
    void this.router.navigate(['/travel/trips', detail.trip.id]);
  }

  closeSheet(): void {
    this.sheetOpen.set(false);
    this.pin.set(null);
    this.lookup.set(null);
  }

  private finishLookup(res: GeoLookup): void {
    this.lookup.set(res);
    this.lookingUp.set(false);
  }

  private loadMarkers(): void {
    this.api.markers().subscribe({ next: (m) => this.markers.set(m) });
  }
}
