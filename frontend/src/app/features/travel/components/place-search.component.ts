import { Component, DestroyRef, OnInit, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { LatLng } from '../map/travel-map.component';
import { GeoLookup, Suggestion, fallbackMessage } from '../models/travel.models';
import { MapsApiService } from '../services/maps-api.service';

/**
 * Google place search box (spec §7, §31): debounced suggestions, then one details lookup on pick.
 * Emits the resolved location; the page decides what to do with it (open the place sheet, add to a trip…).
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
      @if (suggestions().length) {
        <ul class="panel absolute z-[1000] mt-1 w-full p-0 text-sm" role="listbox">
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
  private readonly destroyRef = inject(DestroyRef);
  private readonly query$ = new Subject<string>();

  readonly placeholder = input('Search places');
  /** Biases suggestions toward what the user is looking at (usually the map centre). */
  readonly bias = input<() => LatLng | null>(() => null);
  readonly picked = output<GeoLookup>();

  readonly query = signal('');
  readonly suggestions = signal<Suggestion[]>([]);
  readonly notice = signal<string | null>(null);

  ngOnInit(): void {
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

  onQuery(value: string): void {
    this.query.set(value);
    if (value.trim().length < 3) this.suggestions.set([]);
    this.query$.next(value);
  }

  pick(s: Suggestion): void {
    this.suggestions.set([]);
    this.query.set(s.primary);
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
  }
}

const UNAVAILABLE = 'Search is unavailable right now. Tap the map to save a place.';

function searchFallback(reason: string): string {
  if (reason === 'missing_credential') return 'Place search needs a Google Maps key. Tap the map to save any spot.';
  if (reason === 'cost_protection') return 'Search is paused by maps cost protection. Tap the map to save any spot.';
  return UNAVAILABLE;
}
