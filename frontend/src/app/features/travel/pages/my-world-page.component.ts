import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { MapMarker, TravelMapComponent } from '../map/travel-map.component';
import {
  MAP_LAYERS,
  MapLayer,
  PLACE_STATUS_LABELS,
  PlaceHistory,
  WorldOverview,
  markerColor,
  markerLayer,
} from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';

/** My World (spec §20): the lifetime travel map; selecting a place shows its accumulated history. */
@Component({
  selector: 'app-travel-my-world-page',
  standalone: true,
  imports: [RouterLink, TravelMapComponent],
  template: `
    <div class="space-y-3">
      @if (world(); as w) {
        <div class="grid grid-cols-2 gap-2 text-center text-sm sm:grid-cols-4 lg:grid-cols-8">
          @for (tile of tiles(); track tile.label) {
            <div class="panel">
              <p class="text-lg font-semibold">{{ tile.value }}</p>
              <p class="text-xs" style="color: var(--text-muted)">{{ tile.label }}</p>
            </div>
          }
        </div>
      }
      <div class="flex flex-wrap gap-1.5" role="group" aria-label="Map layers">
        @for (l of layers; track l.id) {
          <button
            type="button"
            class="chip cursor-pointer"
            [attr.aria-pressed]="visible().has(l.id)"
            [style.background]="visible().has(l.id) ? 'var(--primary-soft)' : null"
            (click)="toggle(l.id)"
          >
            {{ visible().has(l.id) ? '☑' : '☐' }} {{ l.label }}
          </button>
        }
      </div>
      <div class="grid gap-3 lg:grid-cols-[2fr_1fr]">
        <app-travel-map class="h-[60vh]" [markers]="markers()" (markerSelect)="select($event)" />
        <div class="panel space-y-2 text-sm">
          @if (history(); as h) {
            <p class="text-base font-semibold uppercase">{{ h.place.name }}</p>
            <p>{{ statusLabels[h.place.status] }}</p>
            <div>
              <p class="text-xs font-medium">Trips</p>
              @for (t of h.trips; track t.id) {
                <p class="text-xs">• <a class="underline" [routerLink]="['/travel/trips', t.id]">{{ t.name }}</a></p>
              } @empty {
                <p class="text-xs" style="color: var(--text-muted)">None yet</p>
              }
            </div>
            <p class="text-xs">Photos: {{ h.photo_count }}</p>
            <p class="text-xs">Journal: {{ h.journal_count }} entries</p>
            <p class="text-xs">Routes: {{ h.route_ids.length }}</p>
            <a class="text-xs underline" [routerLink]="['/travel/places', h.place.id]">Open place</a>
          } @else {
            <p class="text-xs" style="color: var(--text-muted)">Select a place on the map to see its history.</p>
          }
        </div>
      </div>
    </div>
  `,
})
export class MyWorldPageComponent implements OnInit {
  private readonly api = inject(TravelApiService);
  private readonly router = inject(Router);

  readonly layers = MAP_LAYERS;
  readonly statusLabels = PLACE_STATUS_LABELS;
  readonly world = signal<WorldOverview | null>(null);
  readonly history = signal<PlaceHistory | null>(null);
  readonly visible = signal<ReadonlySet<MapLayer>>(new Set(MAP_LAYERS.map((l) => l.id)));

  readonly markers = computed<MapMarker[]>(() =>
    (this.world()?.markers ?? [])
      .filter((m) => this.visible().has(markerLayer(m)))
      .map((m) => ({ id: m.id, kind: m.kind, lat: m.lat, lng: m.lng, label: m.label, color: markerColor(m) })),
  );

  readonly tiles = computed(() => {
    const c = this.world()?.counts;
    if (!c) return [];
    return [
      { label: 'Wishlist', value: c.wishlist },
      { label: 'Planned', value: c.planned },
      { label: 'Visited', value: c.visited },
      { label: 'Favourite', value: c.favourite },
      { label: 'Trips', value: c.trips },
      { label: 'Completed trips', value: c.completed_trips },
      { label: 'Adventures', value: c.adventures },
      { label: 'Photos on map', value: c.photos },
    ];
  });

  ngOnInit(): void {
    this.api.world().subscribe({ next: (w) => this.world.set(w) });
  }

  toggle(id: MapLayer): void {
    const next = new Set(this.visible());
    if (next.has(id)) next.delete(id);
    else next.add(id);
    this.visible.set(next);
  }

  select(marker: MapMarker): void {
    switch (marker.kind) {
      case 'place':
        this.api.placeHistory(marker.id).subscribe({ next: (h) => this.history.set(h) });
        break;
      case 'trip':
        void this.router.navigate(['/travel/trips', marker.id]);
        break;
      case 'adventure':
        void this.router.navigate(['/travel/adventures', marker.id]);
        break;
      case 'photo':
        void this.router.navigate(['/travel/memories']);
        break;
    }
  }
}
