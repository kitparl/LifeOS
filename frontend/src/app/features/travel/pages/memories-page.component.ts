import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../../environments/environment';
import { apiErrorMessage } from '../../../core/utils/http';
import { FileImageSrcDirective } from '../../../shared/markdown/file-image-src.directive';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { PhotoUploadComponent } from '../components/photo-upload.component';
import { MapMarker, TravelMapComponent } from '../map/travel-map.component';
import { JournalEntry, Place, TravelPhoto, TripListItem } from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';

type View = 'photos' | 'map' | 'journal';

/** Memories (spec §17–§19): photos, the photo map and the travel journal, optionally for one trip. */
@Component({
  selector: 'app-travel-memories-page',
  standalone: true,
  imports: [FormsModule, DatePipe, FileImageSrcDirective, ModalComponent, PhotoUploadComponent, TravelMapComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center gap-2">
        <select class="input-field !w-auto text-xs" aria-label="Trip" [ngModel]="tripId()" (ngModelChange)="setTrip($event)">
          <option value="">All trips</option>
          @for (t of trips(); track t.id) {
            <option [value]="t.id">{{ t.name }}</option>
          }
        </select>
        @for (v of views; track v.id) {
          <button type="button" class="text-xs" [class.btn-primary]="view() === v.id" [class.btn-secondary]="view() !== v.id" (click)="view.set(v.id)">{{ v.label }}</button>
        }
      </div>

      @switch (view()) {
        @case ('photos') {
          <app-travel-photo-upload [tripId]="tripId() || null" (uploaded)="load()" />
          <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5" appFileImageSrc>
            @for (p of photos(); track p.id) {
              <button type="button" class="panel p-1 text-left text-xs" (click)="selected.set(p)">
                <img [src]="contentUrl(p.file_id)" [alt]="p.caption || 'Travel photo'" class="h-28 w-full rounded object-cover" loading="lazy" />
                <span class="mt-1 block truncate">{{ p.caption || (p.taken_at | date: 'mediumDate') || 'Photo' }}</span>
              </button>
            } @empty {
              <p class="col-span-full text-xs" style="color: var(--text-muted)">No photos yet.</p>
            }
          </div>
        }
        @case ('map') {
          <app-travel-map class="h-[60vh]" [markers]="photoMarkers()" (markerSelect)="openMarker($event.id)" />
          <p class="text-xs" style="color: var(--text-muted)">Only photos with a confirmed location appear on the map.</p>
        }
        @case ('journal') {
          <form class="panel space-y-2 text-sm" (submit)="$event.preventDefault(); saveEntry()">
            <div class="flex flex-wrap gap-2">
              <input class="input-field !w-auto" type="date" name="date" aria-label="Date" [(ngModel)]="entry.entry_date" />
              <input class="input-field min-w-[12rem] flex-1" name="title" maxlength="200" placeholder="June 17 — Trek Day 2" aria-label="Title" [(ngModel)]="entry.title" />
              <select class="input-field !w-auto" name="place" aria-label="Place" [(ngModel)]="entry.place_id">
                <option [ngValue]="null">No place</option>
                @for (p of places(); track p.id) {
                  <option [ngValue]="p.id">{{ p.name }}</option>
                }
              </select>
            </div>
            <textarea class="input-field" name="content" rows="4" placeholder="Started at 6:20 AM…" aria-label="Entry" [(ngModel)]="entry.content"></textarea>
            <div class="flex gap-2">
              <button type="submit" class="btn-primary text-xs" [disabled]="!entry.title.trim() || !entry.entry_date">{{ editingId ? 'Save entry' : 'Add entry' }}</button>
              @if (editingId) {
                <button type="button" class="btn-secondary text-xs" (click)="resetEntry()">Cancel</button>
              }
            </div>
          </form>
          @for (e of journal(); track e.id) {
            <article class="panel space-y-1 text-sm">
              <div class="flex flex-wrap items-baseline justify-between gap-2">
                <p class="font-medium">{{ e.entry_date | date: 'MMM d, y' }} — {{ e.title }}</p>
                <div class="flex gap-2 text-xs">
                  <button type="button" class="underline" (click)="edit(e)">Edit</button>
                  <button type="button" style="color: var(--danger)" (click)="removeEntry(e.id)">Delete</button>
                </div>
              </div>
              <p class="whitespace-pre-line">{{ e.content }}</p>
            </article>
          } @empty {
            <p class="text-xs" style="color: var(--text-muted)">No journal entries yet.</p>
          }
        }
      }
      @if (error()) {
        <p class="text-xs" style="color: var(--danger)">{{ error() }}</p>
      }

      <app-modal [open]="!!selected()" [title]="selected()?.caption || 'Photo'" maxWidth="40rem" (closed)="selected.set(null)">
        <ng-container body>
          @if (selected(); as p) {
            <div class="space-y-2 text-sm" appFileImageSrc>
              <img [src]="contentUrl(p.file_id)" [alt]="p.caption || 'Travel photo'" class="max-h-[60vh] w-full rounded object-contain" />
              <p class="text-xs" style="color: var(--text-muted)">
                @if (p.taken_at) { {{ p.taken_at | date: 'medium' }} · }
                @if (placeName(p.place_id); as n) { 📍 {{ n }} · }
                @if (tripName(p.trip_id); as n) { 🧳 {{ n }} · }
                {{ p.lat !== null ? 'On the map (' + (p.location_source === 'exif' ? 'from photo' : 'set by you') + ')' : 'No location' }}
              </p>
            </div>
          }
        </ng-container>
        <ng-container footer>
          <button type="button" class="text-xs" style="color: var(--danger)" (click)="removePhoto()">Delete photo</button>
        </ng-container>
      </app-modal>
    </div>
  `,
})
export class MemoriesPageComponent implements OnInit {
  private readonly api = inject(TravelApiService);

  readonly views: { id: View; label: string }[] = [
    { id: 'photos', label: 'Photos' },
    { id: 'map', label: 'Photo map' },
    { id: 'journal', label: 'Journal' },
  ];
  readonly view = signal<View>('photos');
  readonly tripId = signal('');
  readonly trips = signal<TripListItem[]>([]);
  readonly places = signal<Place[]>([]);
  readonly photos = signal<TravelPhoto[]>([]);
  readonly journal = signal<JournalEntry[]>([]);
  readonly selected = signal<TravelPhoto | null>(null);
  readonly error = signal<string | null>(null);
  entry = emptyEntry();
  editingId: string | null = null;

  readonly photoMarkers = computed<MapMarker[]>(() =>
    this.photos()
      .filter((p) => p.lat !== null && p.lng !== null)
      .map((p) => ({ id: p.id, kind: 'photo', lat: p.lat!, lng: p.lng!, label: `📷 ${p.caption ?? 'Photo'}`, color: '--text-muted' })),
  );

  ngOnInit(): void {
    this.api.listTrips({ limit: 100 }).subscribe({ next: (page) => this.trips.set(page.items) });
    this.api.listPlaces({ limit: 100 }).subscribe({ next: (page) => this.places.set(page.items) });
    this.load();
  }

  contentUrl(fileId: string): string {
    return `${environment.apiUrl}/files/${fileId}/content`;
  }

  setTrip(id: string): void {
    this.tripId.set(id);
    this.load();
  }

  load(): void {
    const trip_id = this.tripId() || undefined;
    this.api.listPhotos({ trip_id, limit: 100 }).subscribe({ next: (page) => this.photos.set(page.items) });
    this.api.listJournal({ trip_id, limit: 100 }).subscribe({ next: (page) => this.journal.set(page.items) });
  }

  openMarker(id: string): void {
    this.selected.set(this.photos().find((p) => p.id === id) ?? null);
  }

  placeName(id: string | null): string | null {
    return id ? (this.places().find((p) => p.id === id)?.name ?? null) : null;
  }

  tripName(id: string | null): string | null {
    return id ? (this.trips().find((t) => t.id === id)?.name ?? null) : null;
  }

  removePhoto(): void {
    const p = this.selected();
    if (!p) return;
    this.api.deletePhoto(p.id).subscribe({
      next: () => {
        this.selected.set(null);
        this.load();
      },
      error: (err) => this.error.set(apiErrorMessage(err, 'Could not delete the photo')),
    });
  }

  edit(e: JournalEntry): void {
    this.editingId = e.id;
    this.entry = { entry_date: e.entry_date, title: e.title, content: e.content, place_id: e.place_id };
  }

  resetEntry(): void {
    this.editingId = null;
    this.entry = emptyEntry();
  }

  saveEntry(): void {
    const body = { ...this.entry, title: this.entry.title.trim(), trip_id: this.tripId() || null };
    const request = this.editingId ? this.api.updateJournal(this.editingId, body) : this.api.createJournal(body);
    request.subscribe({
      next: () => {
        this.resetEntry();
        this.load();
      },
      error: (err) => this.error.set(apiErrorMessage(err, 'Could not save the entry')),
    });
  }

  removeEntry(id: string): void {
    this.api.deleteJournal(id).subscribe({ next: () => this.load() });
  }
}

function emptyEntry(): { entry_date: string; title: string; content: string; place_id: string | null } {
  return { entry_date: new Date().toISOString().slice(0, 10), title: '', content: '', place_id: null };
}
