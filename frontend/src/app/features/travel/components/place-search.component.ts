import { Component, DestroyRef, OnInit, computed, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Subject, catchError, debounceTime, distinctUntilChanged, map, of, switchMap } from 'rxjs';
import { LatLng } from '../map/travel-map.component';
import { GeoLookup, Place, Suggestion, TripPlace, fallbackMessage } from '../models/travel.models';
import { MapsApiService, SEARCH_DEBOUNCE_MS } from '../services/maps-api.service';
import { TravelApiService } from '../services/travel-api.service';

/** A place that is already saved, picked from the "On this trip" or "Saved" group. */
export interface PickedPlace {
  id: string;
  name: string;
}

const SAVED_LIMIT = 8;

/**
 * Place search box (spec §7, §31): debounced Google suggestions, then one details lookup on pick.
 * Emits the resolved location; the page decides what to do with it (open the place sheet, add to a trip…).
 * Inside a trip it also searches what is already there — pass `tripPlaces` for "On this trip" and
 * `includeSaved` for the saved library (places already on the trip are hidden from it) — so local
 * hits come first and Google is the last resort.
 */
@Component({
  selector: 'app-place-search',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="relative">
      <input
        class="input-field"
        type="search"
        [placeholder]="placeholder()"
        aria-label="Search places"
        [ngModel]="query()"
        (ngModelChange)="onQuery($event)"
      />
      @if (open() && hasResults()) {
        <ul class="panel absolute z-[1000] mt-1 max-h-72 w-full overflow-y-auto p-0 text-sm" role="listbox">
          @if (tripMatches().length) {
            <li class="px-3 pt-2 text-xs font-medium" style="color: var(--text-muted)">On this trip</li>
            @for (p of tripMatches(); track p.id) {
              <li>
                <button type="button" class="w-full px-3 py-2 text-left" (click)="pickPlace(p)">
                  <span class="font-medium">{{ p.name }}</span>
                </button>
              </li>
            }
          }
          @if (savedMatches().length) {
            <li class="px-3 pt-2 text-xs font-medium" style="color: var(--text-muted)">Saved</li>
            @for (p of savedMatches(); track p.id) {
              <li>
                <button type="button" class="w-full px-3 py-2 text-left" (click)="pickPlace(p)">
                  <span class="font-medium">{{ p.name }}</span>
                  @if (p.city || p.country) {
                    <span class="text-xs" style="color: var(--text-muted)"> · {{ p.city || p.country }}</span>
                  }
                </button>
              </li>
            }
          }
          @if (suggestions().length) {
            <li class="px-3 pt-2 text-xs font-medium" style="color: var(--text-muted)">Nearby / Google</li>
            @for (s of suggestions(); track s.external_place_id) {
              <li>
                <button type="button" class="w-full px-3 py-2 text-left" (click)="pick(s)">
                  <span class="font-medium">{{ s.primary }}</span>
                  @if (s.secondary) {
                    <span class="text-xs" style="color: var(--text-muted)"> · {{ s.secondary }}</span>
                  }
                </button>
              </li>
            }
          }
        </ul>
      }
      @if (notice(); as n) {
        <p class="mt-1 text-xs" style="color: var(--text-muted)">{{ n }}</p>
      }
    </div>
  `,
})
export class PlaceSearchComponent implements OnInit {
  private readonly maps = inject(MapsApiService);
  private readonly api = inject(TravelApiService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly query$ = new Subject<string>();

  readonly placeholder = input('Search places');
  /** Biases suggestions toward what the user is looking at (usually the map centre). */
  readonly bias = input<() => LatLng | null>(() => null);
  /** Places already on the trip; when set, matching ones are listed first under "On this trip". */
  readonly tripPlaces = input<readonly TripPlace[] | null>(null);
  /** Also search the saved library (places already on the trip are left out of it). */
  readonly includeSaved = input(false);
  /** Empty the box after a pick, so several places can be picked one after another. */
  readonly clearOnPick = input(false);
  /** A Google result, resolved to a location. */
  readonly picked = output<GeoLookup>();
  /** A place that is already saved. */
  readonly pickedPlace = output<PickedPlace>();

  readonly query = signal('');
  readonly open = signal(false);
  readonly suggestions = signal<Suggestion[]>([]);
  private readonly saved = signal<Place[]>([]);
  readonly notice = signal<string | null>(null);

  readonly tripMatches = computed(() => {
    const q = this.query().trim().toLowerCase();
    return q ? (this.tripPlaces() ?? []).filter((p) => p.name.toLowerCase().includes(q)) : [];
  });
  readonly savedMatches = computed(() => {
    const onTrip = new Set((this.tripPlaces() ?? []).map((p) => p.id));
    return this.saved().filter((p) => !onTrip.has(p.id));
  });
  readonly hasResults = computed(() => !!(this.tripMatches().length || this.savedMatches().length || this.suggestions().length));

  ngOnInit(): void {
    if (this.includeSaved()) this.watchSaved();
    this.maps
      .searchSuggestions(this.query$, () => this.bias()())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (res) => {
          this.suggestions.set(res.suggestions);
          this.notice.set(res.fallback_reason ? searchFallback(res.fallback_reason) : null);
        },
        error: () => this.notice.set(UNAVAILABLE),
      });
  }

  private watchSaved(): void {
    this.query$
      .pipe(
        map((q) => q.trim()),
        debounceTime(SEARCH_DEBOUNCE_MS),
        distinctUntilChanged(),
        switchMap((q) =>
          q ? this.api.listPlaces({ q, limit: SAVED_LIMIT }).pipe(map((page) => page.items), catchError(() => of<Place[]>([]))) : of<Place[]>([]),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((items) => this.saved.set(items));
  }

  onQuery(value: string): void {
    this.query.set(value);
    this.open.set(true);
    if (value.trim().length < 3) this.suggestions.set([]);
    if (!value.trim()) this.saved.set([]);
    this.query$.next(value);
  }

  pickPlace(place: PickedPlace): void {
    this.finishPick(place.name);
    this.pickedPlace.emit({ id: place.id, name: place.name });
  }

  pick(s: Suggestion): void {
    this.finishPick(s.primary);
    this.maps.placeDetails(s.external_place_id).subscribe({
      next: (res) => {
        if (res.result) this.picked.emit(res);
        else this.notice.set(fallbackMessage(res.fallback_reason));
      },
      error: () => this.notice.set(UNAVAILABLE),
    });
  }

  clear(): void {
    this.query.set('');
    this.suggestions.set([]);
    this.saved.set([]);
  }

  private finishPick(name: string): void {
    this.open.set(false);
    this.suggestions.set([]);
    this.saved.set([]);
    this.query.set(this.clearOnPick() ? '' : name);
    // Let the same text be searched again after the box was emptied (the streams drop repeats).
    if (this.clearOnPick()) this.query$.next('');
  }
}

const UNAVAILABLE = 'Search is unavailable right now. Tap the map to save a place.';

function searchFallback(reason: string): string {
  if (reason === 'missing_credential') return 'Place search needs a Google Maps key. Tap the map to save any spot.';
  if (reason === 'cost_protection') return 'Search is paused by maps cost protection. Tap the map to save any spot.';
  return UNAVAILABLE;
}
