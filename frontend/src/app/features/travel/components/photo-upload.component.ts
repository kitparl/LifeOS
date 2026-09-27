import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { apiErrorMessage } from '../../../core/utils/http';
import { TravelPhoto } from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';
import { PhotoExif, readPhotoExif } from '../utils/photo-exif';

/**
 * Add a travel photo (spec §17): GPS detected → suggest location → user confirms/edits → upload.
 * Location is only sent when the user ticks "Use this location" (private by default, requirements D-08).
 */
@Component({
  selector: 'app-travel-photo-upload',
  standalone: true,
  imports: [FormsModule, DatePipe, DecimalPipe],
  template: `
    <div class="panel space-y-2 text-sm">
      <label class="form-label" for="travel-photo">Add a photo</label>
      <input id="travel-photo" type="file" accept="image/*" (change)="pick($event)" />
      @if (file()) {
        @if (reading()) {
          <p class="text-xs" style="color: var(--text-muted)">Reading photo details…</p>
        }
        @if (!reading() && exif(); as e) {
          @if (e.lat !== null) {
            <label class="flex items-center gap-2 text-xs">
              <input type="checkbox" [(ngModel)]="useLocation" />
              📍 GPS detected ({{ e.lat | number: '1.4-4' }}, {{ e.lng | number: '1.4-4' }}) — use this location
            </label>
          } @else {
            <p class="text-xs" style="color: var(--text-muted)">No location in this photo. It will be saved without one.</p>
          }
          @if (e.takenAt) {
            <p class="text-xs" style="color: var(--text-muted)">Taken {{ e.takenAt | date: 'medium' }}</p>
          }
        }
        <input class="input-field text-xs" maxlength="500" placeholder="Caption" aria-label="Caption" [(ngModel)]="caption" />
        <button type="button" class="btn-primary text-xs" [disabled]="busy() || reading()" (click)="upload()">{{ busy() ? 'Uploading…' : 'Upload' }}</button>
      }
      @if (error()) {
        <p class="text-xs" style="color: var(--danger)">{{ error() }}</p>
      }
    </div>
  `,
})
export class PhotoUploadComponent {
  private readonly api = inject(TravelApiService);

  readonly tripId = input<string | null>(null);
  readonly placeId = input<string | null>(null);
  readonly adventureId = input<string | null>(null);
  readonly journalEntryId = input<string | null>(null);
  readonly uploaded = output<TravelPhoto>();

  readonly file = signal<File | null>(null);
  readonly exif = signal<PhotoExif | null>(null);
  readonly reading = signal(false);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  useLocation = false;
  caption = '';

  async pick(event: Event): Promise<void> {
    const file = (event.target as HTMLInputElement).files?.[0] ?? null;
    this.file.set(file);
    this.exif.set(null);
    this.error.set(null);
    this.useLocation = false;
    if (!file) return;
    this.reading.set(true);
    const exif = await readPhotoExif(file);
    this.exif.set(exif);
    this.useLocation = exif.lat !== null; // suggested; the user can untick before uploading
    this.reading.set(false);
  }

  upload(): void {
    const file = this.file();
    if (!file) return;
    const exif = this.exif();
    const located = this.useLocation && exif?.lat != null && exif.lng != null;
    this.busy.set(true);
    this.api
      .uploadPhoto(file, {
        lat: located ? exif!.lat : null,
        lng: located ? exif!.lng : null,
        location_source: located ? 'exif' : null,
        taken_at: exif?.takenAt ?? null,
        caption: this.caption.trim() || null,
        trip_id: this.tripId(),
        place_id: this.placeId(),
        adventure_id: this.adventureId(),
        journal_entry_id: this.journalEntryId(),
      })
      .subscribe({
        next: (photo) => {
          this.busy.set(false);
          this.file.set(null);
          this.caption = '';
          this.uploaded.emit(photo);
        },
        error: (err) => {
          this.busy.set(false);
          this.error.set(apiErrorMessage(err, 'Could not upload the photo'));
        },
      });
  }
}
