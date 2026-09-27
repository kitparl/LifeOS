import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { apiErrorMessage } from '../../../core/utils/http';
import { TRIP_STATUS_LABELS, TripListItem, TripStatus } from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';

const GROUPS: readonly TripStatus[] = ['active', 'booked', 'planning', 'draft', 'completed'];

/** Trips (spec §10), grouped by status; drafts are clearly marked (requirements D-12). */
@Component({
  selector: 'app-travel-trips-page',
  standalone: true,
  imports: [FormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-3">
      <form class="panel flex flex-wrap items-end gap-2 text-sm" (submit)="$event.preventDefault(); create()">
        <div class="flex min-w-[12rem] flex-1 flex-col gap-1">
          <label class="form-label" for="trip-name">New trip</label>
          <input id="trip-name" name="name" class="input-field" maxlength="200" placeholder="e.g. Himachal 2027" [(ngModel)]="name" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="form-label" for="trip-start">Start (optional)</label>
          <input id="trip-start" name="start" class="input-field" type="date" [(ngModel)]="start" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="form-label" for="trip-end">End (optional)</label>
          <input id="trip-end" name="end" class="input-field" type="date" [(ngModel)]="end" />
        </div>
        <button type="submit" class="btn-primary text-xs" [disabled]="!name.trim() || busy()">Start a draft</button>
        @if (error()) {
          <p class="w-full text-xs" style="color: var(--danger)">{{ error() }}</p>
        }
      </form>

      @if (loading()) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (!trips().length) {
        <p class="text-sm" style="color: var(--text-muted)">No trips yet. Start a draft — you can confirm it when the plan is ready.</p>
      }
      @for (group of grouped(); track group.status) {
        <section class="space-y-2">
          <h3 class="text-sm font-semibold">{{ labels[group.status] }}</h3>
          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            @for (t of group.trips; track t.id) {
              <div
                class="panel cursor-pointer space-y-1 text-sm"
                [style.border-style]="t.status === 'draft' ? 'dashed' : null"
                role="link"
                tabindex="0"
                (click)="open(t.id)"
                (keydown.enter)="open(t.id)"
              >
                <div class="flex items-start justify-between gap-2">
                  <span class="font-medium text-[var(--xp-blue)] underline">🧳 {{ t.name }}</span>
                  <span class="chip text-xs">{{ labels[t.status] }}</span>
                </div>
                <p class="text-xs" style="color: var(--text-muted)">
                  @if (t.start_date) {
                    {{ t.start_date | date: 'MMM d' }} → {{ t.end_date | date: 'MMM d, y' }}
                    @if (t.dates_tentative && t.status === 'draft') { (tentative) }
                  } @else {
                    Dates not set
                  }
                  · {{ t.place_count }} places
                </p>
              </div>
            }
          </div>
        </section>
      }
    </div>
  `,
})
export class TripsPageComponent implements OnInit {
  private readonly api = inject(TravelApiService);
  private readonly router = inject(Router);

  readonly labels = TRIP_STATUS_LABELS;
  readonly trips = signal<TripListItem[]>([]);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  name = '';
  start = '';
  end = '';

  readonly grouped = computed(() =>
    GROUPS.map((status) => ({ status, trips: this.trips().filter((t) => t.status === status) })).filter(
      (g) => g.trips.length,
    ),
  );

  ngOnInit(): void {
    this.loading.set(true);
    this.api.listTrips({ limit: 100 }).subscribe({
      next: (page) => {
        this.trips.set(page.items);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  create(): void {
    this.busy.set(true);
    this.error.set(null);
    this.api
      .createTrip({ name: this.name.trim(), start_date: this.start || null, end_date: this.end || null })
      .subscribe({
        next: (detail) => void this.router.navigate(['/travel/trips', detail.trip.id]),
        error: (err) => {
          this.busy.set(false);
          this.error.set(apiErrorMessage(err, 'Could not create the trip'));
        },
      });
  }

  open(id: string): void {
    void this.router.navigate(['/travel/trips', id]);
  }
}
