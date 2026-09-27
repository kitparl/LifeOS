import { Component, effect, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { apiErrorMessage } from '../../../core/utils/http';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { TRIP_STATUS_LABELS, TripDetail, TripListItem } from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';

/** "Add to Trip" (spec §12): pick an open trip — or start a new draft — then optionally a day. */
@Component({
  selector: 'app-trip-picker',
  standalone: true,
  imports: [FormsModule, ModalComponent],
  template: `
    <app-modal [open]="open()" title="Add to trip" maxWidth="26rem" (closed)="closed.emit()">
      <ng-container body>
        <div class="space-y-3 text-sm">
          <p class="text-xs" style="color: var(--text-muted)">Adding <strong>{{ placeName() }}</strong></p>
          <div class="flex flex-col gap-1">
            <label class="form-label" for="trip-pick">Trip</label>
            <select id="trip-pick" class="input-field" [(ngModel)]="tripId" (ngModelChange)="loadDays($event)">
              <option value="">＋ New draft trip…</option>
              @for (t of trips(); track t.id) {
                <option [value]="t.id">{{ t.name }} ({{ statusLabels[t.status] }})</option>
              }
            </select>
          </div>
          @if (!tripId) {
            <input class="input-field" maxlength="200" placeholder="Trip name, e.g. Himachal 2027" aria-label="New trip name" [(ngModel)]="newName" />
          } @else if (days().length) {
            <div class="flex flex-col gap-1">
              <label class="form-label" for="day-pick">Day (optional)</label>
              <select id="day-pick" class="input-field" [(ngModel)]="dayId">
                <option value="">Not on a day yet</option>
                @for (d of days(); track d.id) {
                  <option [value]="d.id">Day {{ d.day_index + 1 }}{{ d.day_date ? ' · ' + d.day_date : '' }}</option>
                }
              </select>
            </div>
          }
          @if (error()) {
            <p class="text-xs" style="color: var(--danger)">{{ error() }}</p>
          }
        </div>
      </ng-container>
      <ng-container footer>
        <div class="flex justify-end gap-2">
          <button type="button" class="btn-secondary text-xs" (click)="closed.emit()">Cancel</button>
          <button type="button" class="btn-primary text-xs" [disabled]="busy() || (!tripId && !newName.trim())" (click)="submit()">Add</button>
        </div>
      </ng-container>
    </app-modal>
  `,
})
export class TripPickerComponent {
  private readonly api = inject(TravelApiService);

  readonly open = input(false);
  readonly placeId = input<string | null>(null);
  readonly placeName = input('');
  readonly added = output<TripDetail>();
  readonly closed = output<void>();

  readonly statusLabels = TRIP_STATUS_LABELS;
  readonly trips = signal<TripListItem[]>([]);
  readonly days = signal<TripDetail['days']>([]);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  tripId = '';
  dayId = '';
  newName = '';

  constructor() {
    effect(() => {
      if (!this.open()) return;
      this.error.set(null);
      this.api.listTrips({ limit: 100 }).subscribe({
        next: (page) => {
          const open = page.items.filter((t) => t.status !== 'completed');
          this.trips.set(open);
          this.tripId = open[0]?.id ?? '';
          this.loadDays(this.tripId);
        },
      });
    });
  }

  loadDays(tripId: string): void {
    this.dayId = '';
    this.days.set([]);
    if (tripId) this.api.getTrip(tripId).subscribe({ next: (d) => this.days.set(d.days) });
  }

  submit(): void {
    const placeId = this.placeId();
    if (!placeId) return;
    this.busy.set(true);
    const addTo = (tripId: string) =>
      this.api.addPlaceToTrip(tripId, placeId, this.dayId || null).subscribe({
        next: (detail) => {
          this.busy.set(false);
          this.added.emit(detail);
        },
        error: (err) => this.fail(err),
      });
    if (this.tripId) {
      addTo(this.tripId);
      return;
    }
    this.api.createTrip({ name: this.newName.trim() }).subscribe({
      next: (created) => addTo(created.trip.id),
      error: (err) => this.fail(err),
    });
  }

  private fail(err: unknown): void {
    this.busy.set(false);
    this.error.set(apiErrorMessage(err, 'Could not add to the trip'));
  }
}
