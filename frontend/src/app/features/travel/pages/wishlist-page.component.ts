import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ChipOption, ChipRowComponent } from '../../../shared/chip-row/chip-row.component';
import { ListPaginatorComponent } from '../../../shared/pagination/list-paginator.component';
import { MapMarker, TravelMapComponent } from '../map/travel-map.component';
import { PLACE_CATEGORIES, PLACE_STATUS_COLORS, Place } from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';

type View = 'map' | 'list' | 'grid';

const CATEGORY_FILTERS: readonly ChipOption[] = [
  { id: '', label: 'All' },
  ...PLACE_CATEGORIES.filter((c) => c.id !== 'other'),
];
/** The map view shows the whole wishlist; one request is plenty at personal scale. */
const MAP_VIEW_LIMIT = 100;

/** Travel Wishlist (spec §9): places with status WISHLIST, as map / list / grid. */
@Component({
  selector: 'app-travel-wishlist-page',
  standalone: true,
  imports: [RouterLink, ChipRowComponent, ListPaginatorComponent, TravelMapComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h2 class="text-base font-semibold">Travel Wishlist</h2>
        <div class="flex gap-1" role="group" aria-label="View">
          @for (v of views; track v) {
            <button
              type="button"
              class="text-xs capitalize"
              [class.btn-primary]="view() === v"
              [class.btn-secondary]="view() !== v"
              (click)="setView(v)"
            >
              {{ v }}
            </button>
          }
        </div>
      </div>
      <app-chip-row label="Category" [options]="categories" [selected]="category()" testIdPrefix="travel-cat" (selectedChange)="setCategory($event)" />

      @if (loading()) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (total() === 0) {
        <div class="panel text-sm">
          <p style="color: var(--text-muted)">Your Travel Wishlist is empty.</p>
          <a routerLink="/travel/map" class="btn-primary mt-2 inline-block text-xs no-underline">Open the map and tap a place</a>
        </div>
      } @else if (view() === 'map') {
        <app-travel-map class="h-[60vh]" [markers]="markers()" (markerSelect)="open($event.id)" />
      } @else {
        <div [class]="view() === 'grid' ? 'grid gap-3 sm:grid-cols-2 lg:grid-cols-3' : 'space-y-2'">
          @for (p of places(); track p.id) {
            <div
              class="panel cursor-pointer space-y-1 text-sm"
              role="link"
              tabindex="0"
              (click)="open(p.id)"
              (keydown.enter)="open(p.id)"
            >
              <div class="flex items-start justify-between gap-2">
                <span class="font-medium text-[var(--xp-blue)] underline">{{ p.name }}</span>
                <span class="text-xs capitalize" style="color: var(--text-muted)">{{ categoryLabel(p.category) }}</span>
              </div>
              @if (where(p); as w) {
                <p class="text-xs" style="color: var(--text-muted)">{{ w }}</p>
              }
              @if (p.desired_period || p.estimated_days) {
                <p class="text-xs">
                  @if (p.desired_period) { {{ p.desired_period }} }
                  @if (p.estimated_days) { · {{ p.estimated_days }} days }
                </p>
              }
              @if (p.tags.length) {
                <div class="flex flex-wrap gap-1">
                  @for (t of p.tags; track t) {
                    <span class="chip text-xs">{{ t }}</span>
                  }
                </div>
              }
            </div>
          }
        </div>
        <app-list-paginator [total]="total()" [pageSize]="pageSize" [currentPage]="page()" (pageChange)="setPage($event)" />
      }
    </div>
  `,
})
export class WishlistPageComponent implements OnInit {
  private readonly api = inject(TravelApiService);
  private readonly router = inject(Router);

  readonly views: View[] = ['map', 'list', 'grid'];
  readonly categories = CATEGORY_FILTERS;
  readonly pageSize = 25;
  readonly view = signal<View>('list');
  readonly category = signal('');
  readonly page = signal(1);
  readonly places = signal<Place[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);

  readonly markers = computed<MapMarker[]>(() =>
    this.places().map((p) => ({
      id: p.id,
      kind: 'place',
      lat: p.lat,
      lng: p.lng,
      label: p.name,
      color: PLACE_STATUS_COLORS.wishlist,
    })),
  );

  ngOnInit(): void {
    this.load();
  }

  setView(view: View): void {
    this.view.set(view);
    this.page.set(1);
    this.load();
  }

  setCategory(category: string): void {
    this.category.set(category);
    this.page.set(1);
    this.load();
  }

  setPage(page: number): void {
    this.page.set(page);
    this.load();
  }

  open(id: string): void {
    void this.router.navigate(['/travel/places', id]);
  }

  where(p: Place): string {
    return [p.region, p.country].filter((part): part is string => !!part).join(', ');
  }

  categoryLabel(id: string): string {
    return PLACE_CATEGORIES.find((c) => c.id === id)?.label ?? id;
  }

  private load(): void {
    const mapView = this.view() === 'map';
    const limit = mapView ? MAP_VIEW_LIMIT : this.pageSize;
    this.loading.set(true);
    this.api
      .listPlaces({
        status: 'wishlist',
        category: this.category() || undefined,
        limit,
        offset: mapView ? 0 : (this.page() - 1) * this.pageSize,
      })
      .subscribe({
        next: (page) => {
          this.places.set(page.items);
          this.total.set(page.total);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }
}
