import { DecimalPipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { apiErrorMessage } from '../../../core/utils/http';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { PhotoUploadComponent } from '../components/photo-upload.component';
import { TripPickerComponent } from '../components/trip-picker.component';
import { MapMarker, TravelMapComponent } from '../map/travel-map.component';
import {
  PLACE_CATEGORIES,
  PLACE_STATUS_COLORS,
  PLACE_STATUS_LABELS,
  Place,
  PlaceCategory,
  PlaceHistory,
  PlaceStatus,
} from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';
import { openInGoogleMapsUrl } from '../utils/google-links';

interface PlaceForm {
  name: string;
  category: PlaceCategory;
  status: PlaceStatus;
  description: string;
  notes: string;
  desired_period: string;
  estimated_days: number | null;
  links: string;
  tags: string;
}

/** A place and everything connected to it (spec §8, §20, §25). */
@Component({
  selector: 'app-travel-place-detail',
  standalone: true,
  imports: [FormsModule, RouterLink, DecimalPipe, TravelMapComponent, TripPickerComponent, PhotoUploadComponent],
  template: `
    @if (place(); as p) {
      <div class="grid gap-4 lg:grid-cols-2">
        <div class="space-y-3">
          <div class="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 class="text-base font-semibold">📍 {{ p.name }}</h2>
              @if (p.address) {
                <p class="text-xs" style="color: var(--text-muted)">{{ p.address }}</p>
              }
              <p class="text-xs" style="color: var(--text-muted)">{{ p.lat | number: '1.5-5' }}, {{ p.lng | number: '1.5-5' }}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button type="button" class="btn-secondary text-xs" (click)="picking.set(true)">🧳 Add to Trip</button>
              <a class="btn-primary text-xs no-underline" [href]="googleUrl()" target="_blank" rel="noopener noreferrer">Open in Google Maps</a>
            </div>
          </div>

          <div class="panel space-y-2 text-sm">
            <div class="grid grid-cols-2 gap-2">
              <div class="col-span-2 flex flex-col gap-1">
                <label class="form-label" for="pd-name">Name</label>
                <input id="pd-name" class="input-field" maxlength="200" [(ngModel)]="form.name" />
              </div>
              <div class="flex flex-col gap-1">
                <label class="form-label" for="pd-category">Category</label>
                <select id="pd-category" class="input-field" [(ngModel)]="form.category">
                  @for (c of categories; track c.id) {
                    <option [value]="c.id">{{ c.label }}</option>
                  }
                </select>
              </div>
              <div class="flex flex-col gap-1">
                <label class="form-label" for="pd-status">Status</label>
                <select id="pd-status" class="input-field" [(ngModel)]="form.status">
                  @for (s of statuses; track s[0]) {
                    <option [value]="s[0]">{{ s[1] }}</option>
                  }
                </select>
              </div>
              <div class="flex flex-col gap-1">
                <label class="form-label" for="pd-period">Desired travel period</label>
                <input id="pd-period" class="input-field" maxlength="80" placeholder="e.g. June–September" [(ngModel)]="form.desired_period" />
              </div>
              <div class="flex flex-col gap-1">
                <label class="form-label" for="pd-days">Estimated days</label>
                <input id="pd-days" class="input-field" type="number" min="1" max="365" [(ngModel)]="form.estimated_days" />
              </div>
            </div>
            <div class="flex flex-col gap-1">
              <label class="form-label" for="pd-description">Description</label>
              <textarea id="pd-description" class="input-field" rows="2" [(ngModel)]="form.description"></textarea>
            </div>
            <div class="flex flex-col gap-1">
              <label class="form-label" for="pd-notes">Notes</label>
              <textarea id="pd-notes" class="input-field" rows="3" [(ngModel)]="form.notes"></textarea>
            </div>
            <div class="flex flex-col gap-1">
              <label class="form-label" for="pd-tags">Tags (comma separated)</label>
              <input id="pd-tags" class="input-field" [(ngModel)]="form.tags" placeholder="himachal, monsoon" />
            </div>
            <div class="flex flex-col gap-1">
              <label class="form-label" for="pd-links">External links (one per line)</label>
              <textarea id="pd-links" class="input-field" rows="2" [(ngModel)]="form.links" placeholder="https://…"></textarea>
            </div>
            <div class="flex flex-wrap gap-2">
              <button type="button" class="btn-primary text-xs" [disabled]="busy()" (click)="save()">{{ busy() ? 'Saving…' : 'Save' }}</button>
              <button type="button" class="text-xs" style="color: var(--danger)" [disabled]="busy()" (click)="remove()">Delete</button>
              <a routerLink="/travel/wishlist" class="text-xs underline self-center">Back to Travel Wishlist</a>
            </div>
            @if (message(); as m) {
              <p class="text-xs" [style.color]="m.ok ? 'var(--success)' : 'var(--danger)'">{{ m.text }}</p>
            }
          </div>
        </div>

        <div class="space-y-3">
          <app-travel-map class="h-64" [markers]="marker()" />
          @if (history(); as h) {
            <div class="panel space-y-2 text-sm">
              <p class="font-medium">{{ statusLabel(p.status) }}</p>
              <div>
                <p class="text-xs font-medium">Trips</p>
                @if (h.trips.length) {
                  <ul class="list-disc pl-5 text-xs">
                    @for (t of h.trips; track t.id) {
                      <li><a class="underline" [routerLink]="['/travel/trips', t.id]">{{ t.name }}</a> <span style="color: var(--text-muted)">({{ t.status }})</span></li>
                    }
                  </ul>
                } @else {
                  <p class="text-xs" style="color: var(--text-muted)">Not in any trip yet.</p>
                }
              </div>
              <p class="text-xs">Photos: {{ h.photo_count }} · Journal: {{ h.journal_count }} entries · Routes: {{ h.route_ids.length }}</p>
            </div>
          }
          <app-travel-photo-upload [placeId]="p.id" (uploaded)="refreshHistory(p.id)" />
        </div>
      </div>
      <app-trip-picker
        [open]="picking()"
        [placeId]="p.id"
        [placeName]="p.name"
        (added)="picking.set(false); router.navigate(['/travel/trips', $event.trip.id])"
        (closed)="picking.set(false)"
      />
    } @else if (notFound()) {
      <p class="text-sm">This place does not exist. <a routerLink="/travel/wishlist" class="underline">Back</a></p>
    } @else {
      <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
    }
  `,
})
export class PlaceDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  readonly router = inject(Router);
  private readonly api = inject(TravelApiService);
  private readonly confirm = inject(ConfirmService);

  readonly categories = PLACE_CATEGORIES;
  readonly statuses = Object.entries(PLACE_STATUS_LABELS) as [PlaceStatus, string][];
  readonly place = signal<Place | null>(null);
  readonly history = signal<PlaceHistory | null>(null);
  readonly notFound = signal(false);
  readonly picking = signal(false);
  readonly busy = signal(false);
  readonly message = signal<{ ok: boolean; text: string } | null>(null);
  form: PlaceForm = emptyForm();

  readonly googleUrl = computed(() => {
    const p = this.place();
    return p ? openInGoogleMapsUrl(p) : '';
  });
  readonly marker = computed<MapMarker[]>(() => {
    const p = this.place();
    return p ? [{ id: p.id, kind: 'place', lat: p.lat, lng: p.lng, label: p.name, color: PLACE_STATUS_COLORS[p.status] }] : [];
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.api.placeHistory(id).subscribe({
      next: (h) => {
        this.history.set(h);
        this.apply(h.place);
      },
      error: () => this.notFound.set(true),
    });
  }

  refreshHistory(id: string): void {
    this.api.placeHistory(id).subscribe({ next: (h) => this.history.set(h) });
  }

  statusLabel(status: PlaceStatus): string {
    return PLACE_STATUS_LABELS[status];
  }

  save(): void {
    const p = this.place();
    if (!p) return;
    this.busy.set(true);
    const f = this.form;
    const tags = f.tags.split(',').map((t) => t.trim()).filter(Boolean);
    this.api
      .updatePlace(p.id, {
        name: f.name.trim(),
        category: f.category,
        status: f.status,
        description: f.description.trim() || null,
        notes: f.notes.trim() || null,
        desired_period: f.desired_period.trim() || null,
        estimated_days: f.estimated_days || null,
        links: f.links.split('\n').map((l) => l.trim()).filter(Boolean),
      })
      .subscribe({
        next: () =>
          this.api.setTags(p.id, tags).subscribe({
            next: (updated) => {
              this.apply(updated);
              this.busy.set(false);
              this.message.set({ ok: true, text: 'Saved' });
            },
            error: (err) => this.fail(err),
          }),
        error: (err) => this.fail(err),
      });
  }

  async remove(): Promise<void> {
    const p = this.place();
    if (!p || !(await this.confirm.confirm(`Delete ${p.name}?`, 'Delete place'))) return;
    this.api.deletePlace(p.id).subscribe({
      next: () => void this.router.navigate(['/travel/wishlist']),
      error: (err) => this.fail(err),
    });
  }

  private apply(p: Place): void {
    this.place.set(p);
    this.form = {
      name: p.name,
      category: p.category,
      status: p.status,
      description: p.description ?? '',
      notes: p.notes ?? '',
      desired_period: p.desired_period ?? '',
      estimated_days: p.estimated_days,
      links: p.links.join('\n'),
      tags: p.tags.join(', '),
    };
  }

  private fail(err: unknown): void {
    this.busy.set(false);
    this.message.set({ ok: false, text: apiErrorMessage(err, 'Something went wrong') });
  }
}

function emptyForm(): PlaceForm {
  return {
    name: '',
    category: 'other',
    status: 'wishlist',
    description: '',
    notes: '',
    desired_period: '',
    estimated_days: null,
    links: '',
    tags: '',
  };
}
