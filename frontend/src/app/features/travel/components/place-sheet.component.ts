import { DecimalPipe } from '@angular/common';
import { Component, computed, effect, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ModalComponent } from '../../../shared/modal/modal.component';
import {
  GeoLookup,
  PLACE_CATEGORIES,
  PLACE_STATUS_LABELS,
  PlaceCategory,
  PlaceCreate,
  PlaceStatus,
  fallbackMessage,
} from '../models/travel.models';
import { openInGoogleMapsUrl } from '../utils/google-links';

export type PlaceSheetIntent = 'save' | 'wishlist' | 'trip' | 'waypoint';

export interface PlaceSheetSubmit {
  intent: PlaceSheetIntent;
  place: PlaceCreate;
}

/**
 * Location details after a map tap or a search pick (spec §6). The same form — and the same
 * Place entity — whether Google named the spot or the user types the name (spec §7, fallback D-01).
 */
@Component({
  selector: 'app-place-sheet',
  standalone: true,
  imports: [FormsModule, DecimalPipe, ModalComponent],
  template: `
    <app-modal [open]="open()" [title]="loading() ? 'Finding this place…' : 'Location'" maxWidth="28rem" (closed)="closed.emit()">
      <ng-container body>
        @if (point(); as p) {
          <div class="space-y-3 text-sm">
            @if (notice(); as n) {
              <p class="text-xs rounded p-2" style="background: var(--info-soft); color: var(--text)">{{ n }}</p>
            }
            <div class="flex flex-col gap-1">
              <label class="form-label" for="place-name">Name</label>
              <input id="place-name" class="input-field" maxlength="200" [(ngModel)]="name" placeholder="e.g. Hampta Pass" />
            </div>
            @if (lookup()?.result?.address; as address) {
              <p class="text-xs" style="color: var(--text-muted)">{{ address }}</p>
            }
            <p class="text-xs" style="color: var(--text-muted)">
              Coordinates: {{ p.lat | number: '1.5-5' }}, {{ p.lng | number: '1.5-5' }}
              · <a class="underline" [href]="googleUrl()" target="_blank" rel="noopener noreferrer">Open in Google Maps</a>
            </p>
            <div class="grid grid-cols-2 gap-2">
              <div class="flex flex-col gap-1">
                <label class="form-label" for="place-category">Category</label>
                <select id="place-category" class="input-field" [(ngModel)]="category">
                  @for (c of categories; track c.id) {
                    <option [value]="c.id">{{ c.label }}</option>
                  }
                </select>
              </div>
              <div class="flex flex-col gap-1">
                <label class="form-label" for="place-status">Status</label>
                <select id="place-status" class="input-field" [(ngModel)]="status">
                  @for (s of statuses; track s[0]) {
                    <option [value]="s[0]">{{ s[1] }}</option>
                  }
                </select>
              </div>
            </div>
            @if (error()) {
              <p class="text-xs" style="color: var(--danger)">{{ error() }}</p>
            }
          </div>
        }
      </ng-container>
      <ng-container footer>
        <div class="flex flex-wrap justify-end gap-2">
          <button type="button" class="btn-secondary text-xs" (click)="closed.emit()">Cancel</button>
          @if (allowWaypoint()) {
            <button type="button" class="btn-secondary text-xs" [disabled]="!canSubmit()" (click)="submit('waypoint')">📍 Create Waypoint</button>
          }
          @if (allowTrip()) {
            <button type="button" class="btn-secondary text-xs" [disabled]="!canSubmit()" (click)="submit('trip')">🧳 Add to Trip</button>
          }
          <button type="button" class="btn-secondary text-xs" [disabled]="!canSubmit()" (click)="submit('wishlist')">❤️ Add to Travel Wishlist</button>
          <button type="button" class="btn-primary text-xs" [disabled]="!canSubmit()" (click)="submit('save')">Save Place</button>
        </div>
      </ng-container>
    </app-modal>
  `,
})
export class PlaceSheetComponent {
  readonly open = input(false);
  readonly point = input<{ lat: number; lng: number } | null>(null);
  readonly lookup = input<GeoLookup | null>(null);
  readonly loading = input(false);
  readonly busy = input(false);
  readonly error = input<string | null>(null);
  readonly allowTrip = input(false);
  readonly allowWaypoint = input(false);

  readonly submitted = output<PlaceSheetSubmit>();
  readonly closed = output<void>();

  readonly categories = PLACE_CATEGORIES;
  readonly statuses = Object.entries(PLACE_STATUS_LABELS) as [PlaceStatus, string][];
  name = '';
  category: PlaceCategory = 'other';
  status: PlaceStatus = 'wishlist';

  readonly notice = computed(() => (this.loading() ? null : fallbackMessage(this.lookup()?.fallback_reason ?? null)));
  readonly googleUrl = computed(() => {
    const p = this.point();
    const r = this.lookup()?.result;
    return p ? openInGoogleMapsUrl({ ...p, external_place_id: r?.external_place_id }) : '';
  });

  constructor() {
    // Pre-fill the name whenever a new lookup arrives; a blank name means "type one" (fallback).
    effect(() => {
      const result = this.lookup()?.result;
      this.point();
      this.name = result?.name ?? '';
      this.category = 'other';
      this.status = 'wishlist';
    });
  }

  canSubmit(): boolean {
    return !this.loading() && !this.busy() && this.name.trim().length > 0;
  }

  submit(intent: PlaceSheetIntent): void {
    const p = this.point();
    if (!p || !this.canSubmit()) return;
    const r = this.lookup()?.result;
    this.submitted.emit({
      intent,
      place: {
        name: this.name.trim(),
        lat: p.lat,
        lng: p.lng,
        address: r?.address ?? null,
        country: r?.country ?? null,
        region: r?.region ?? null,
        city: r?.city ?? null,
        external_place_id: r?.external_place_id ?? null,
        category: this.category,
        status: intent === 'wishlist' ? 'wishlist' : this.status,
      },
    });
  }
}
