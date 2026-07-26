import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FileUploadComponent } from '../../shared/file-upload/file-upload.component';
import { TypeSelectComponent } from '../../shared/type-select/type-select.component';
import { FilesService } from '../files/services/files.service';
import { RACE_DISTANCES, RaceEvent } from './models/running.models';
import { RunningService } from './services/running.service';

interface EventPhotoItem {
  url: string;
  preview: string;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function isPastDate(dateStr: string): boolean {
  if (!dateStr) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const raceDate = new Date(`${dateStr}T00:00:00`);
  return raceDate < today;
}

@Component({
  selector: 'app-race-event-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, TypeSelectComponent, FileUploadComponent],
  template: `
    <div style="max-width: 640px">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar">{{ isEdit ? 'Edit Event' : 'Add Race / Competition' }}</div>
        <form class="space-y-4 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">

          <section class="space-y-3">
            <h2 class="text-xs font-semibold uppercase tracking-wide" style="color: var(--text-muted)">Event details</h2>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div class="sm:col-span-2">
                <label class="form-label" for="name">Event Name</label>
                <input id="name" class="input-field mt-1" formControlName="name" placeholder="e.g. TCS World 10K 2026" />
              </div>
              <div>
                <label class="form-label" for="race_date">Date</label>
                <input id="race_date" class="input-field mt-1" type="date" formControlName="race_date" />
              </div>
              <div>
                <label class="form-label" for="distance_type">Distance</label>
                <select id="distance_type" class="input-field mt-1" formControlName="distance_type">
                  @for (d of raceDistances; track d.value) {
                    <option [value]="d.value">{{ d.label }}</option>
                  }
                </select>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label class="form-label" for="organizer">Organizer</label>
                <input id="organizer" class="input-field mt-1" formControlName="organizer" placeholder="Event organizer" />
              </div>
              <div>
                <label class="form-label" for="location">Location / City</label>
                <input id="location" class="input-field mt-1" formControlName="location" placeholder="Bengaluru, India" />
              </div>
            </div>

            <div>
              <label class="form-label">Shoes (optional)</label>
              <div class="mt-1">
                <app-type-select
                  formControlName="shoe"
                  placeholder="Select or create shoes…"
                  [options]="shoes()"
                  (created)="onShoeCreated($event)"
                />
              </div>
            </div>
          </section>

          <section class="space-y-3 border-t pt-4" style="border-color: var(--xp-border)">
            <h2 class="text-xs font-semibold uppercase tracking-wide" style="color: var(--text-muted)">Registration & result</h2>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label class="form-label" for="bib_number">Bib Number</label>
                <input id="bib_number" class="input-field mt-1" formControlName="bib_number" placeholder="e.g. 4521" />
              </div>
              <div>
                <label class="form-label" for="position">Position / Rank</label>
                <input id="position" class="input-field mt-1" type="number" min="1" formControlName="position" placeholder="e.g. 142" />
              </div>
            </div>

            <div class="flex flex-wrap gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" formControlName="registered" class="w-4 h-4" />
                <span class="form-label" style="margin: 0">Registered for event</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" formControlName="attended" class="w-4 h-4" />
                <span class="form-label" style="margin: 0">I attended / completed this race</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" formControlName="medal" class="w-4 h-4" />
                <span class="form-label" style="margin: 0">Medal</span>
              </label>
            </div>

            @if (isPastRaceDate()) {
              <p class="text-xs" style="color: var(--text-muted)">
                Past event — check "I attended" and add your finish time to record the result.
              </p>
            }

            @if (form.controls.attended.value) {
              <div class="finish-time-block">
                <label class="form-label">Finish Time</label>
                <div class="finish-time-row">
                  <div class="finish-time-field">
                    <span class="finish-time-label">Hours</span>
                    <input
                      class="input-field finish-time-input"
                      type="number"
                      min="0"
                      inputmode="numeric"
                      formControlName="finish_hours"
                      placeholder="0"
                    />
                  </div>
                  <span class="finish-time-sep">:</span>
                  <div class="finish-time-field">
                    <span class="finish-time-label">Minutes</span>
                    <input
                      class="input-field finish-time-input"
                      type="number"
                      min="0"
                      max="59"
                      inputmode="numeric"
                      formControlName="finish_minutes"
                      placeholder="00"
                    />
                  </div>
                  <span class="finish-time-sep">:</span>
                  <div class="finish-time-field">
                    <span class="finish-time-label">Seconds</span>
                    <input
                      class="input-field finish-time-input"
                      type="number"
                      min="0"
                      max="59"
                      inputmode="numeric"
                      formControlName="finish_seconds"
                      placeholder="00"
                    />
                  </div>
                </div>
              </div>
            }
          </section>

          <section class="space-y-3 border-t pt-4" style="border-color: var(--xp-border)">
            <h2 class="text-xs font-semibold uppercase tracking-wide" style="color: var(--text-muted)">Media & links</h2>

            <div>
              <label class="form-label mb-1 block">Event images</label>
              @if (eventPhotos.length) {
                <div class="mb-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
                  @for (photo of eventPhotos; track photo.url; let i = $index) {
                    <div class="relative overflow-hidden rounded border border-[var(--xp-border)]">
                      <img [src]="photo.preview || photo.url" alt="Event photo {{ i + 1 }}" class="h-28 w-full object-cover" />
                      <button
                        type="button"
                        class="absolute right-1 top-1 rounded px-1.5 py-0.5 text-[10px]"
                        style="background: var(--surface); color: var(--danger); border: 1px solid var(--xp-border)"
                        (click)="removeEventPhoto(i)"
                      >
                        Remove
                      </button>
                    </div>
                  }
                </div>
              }
              <app-file-upload
                label="Add event photos"
                hint="Images — choose, paste (Ctrl/Cmd+V), or drop (multiple OK)"
                accept="image/*"
                module="running"
                [entityId]="raceId"
                [multiple]="true"
                [knownChecksums]="eventPhotoChecksums"
                (uploaded)="onEventImageUploaded($event)"
              />
            </div>

            <div>
              <label class="form-label mb-1 block">Certificate</label>
              <app-file-upload
                label="Certificate image or PDF"
                hint="Image or PDF — choose, paste, or drop — or use a link below"
                accept="image/*,application/pdf"
                module="running"
                [entityId]="raceId"
                [initialUrl]="certificateFileUrl"
                (uploaded)="onCertificateUploaded($event)"
                (cleared)="onCertificateUploadCleared()"
              />
              <label class="form-label mt-2 mb-1 block" for="certificate_url">Or certificate link</label>
              <input
                id="certificate_url"
                class="input-field"
                type="url"
                formControlName="certificate_url"
                placeholder="https://…"
              />
            </div>

            <div>
              <label class="form-label" for="event_url">Event source link</label>
              <input
                id="event_url"
                class="input-field mt-1"
                type="url"
                formControlName="event_url"
                placeholder="https://event-website.com/…"
              />
              <p class="mt-1 text-xs" style="color: var(--text-muted)">
                Official event page or registration URL
              </p>
            </div>
          </section>

          <section class="space-y-3 border-t pt-4" style="border-color: var(--xp-border)">
            <div>
              <label class="form-label" for="notes">Notes</label>
              <textarea
                id="notes"
                class="input-field mt-1"
                style="min-height: 72px; resize: vertical"
                formControlName="notes"
                placeholder="Race report, conditions, memories…"
              ></textarea>
            </div>
          </section>

          @if (error) {
            <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
          }

          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : isEdit ? 'Update Event' : 'Add Event' }}
            </button>
            <a routerLink="/running" class="btn-secondary no-underline">Cancel</a>
          </div>
        </form>
      </div>
    </div>

    <style>
      .finish-time-block {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
      }
      .finish-time-row {
        display: flex;
        align-items: flex-end;
        gap: 0.5rem;
      }
      .finish-time-field {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
      }
      .finish-time-label {
        font-size: 0.7rem;
        font-weight: 500;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
      }
      .finish-time-input {
        min-height: 44px;
        font-size: 1rem;
        text-align: center;
        font-variant-numeric: tabular-nums;
      }
      .finish-time-sep {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-muted);
        padding-bottom: 0.65rem;
        flex-shrink: 0;
      }
    </style>
  `,
})
export class RaceEventFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly runningService = inject(RunningService);
  private readonly filesService = inject(FilesService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  raceDistances = RACE_DISTANCES;
  shoes = signal<string[]>([]);
  isEdit = false;
  raceId: string | null = null;
  saving = false;
  error = '';
  eventPhotos: EventPhotoItem[] = [];
  eventPhotoChecksums: string[] = [];
  /** Tracks uploaded certificate file URL separately from a typed external link. */
  certificateFileUrl: string | null = null;

  form = this.fb.nonNullable.group({
    name: ['', Validators.required],
    race_date: [todayIsoDate(), Validators.required],
    distance_type: ['marathon' as const, Validators.required],
    organizer: [''],
    location: [''],
    shoe: [''],
    bib_number: [''],
    finish_hours: [null as number | null, [Validators.min(0)]],
    finish_minutes: [null as number | null, [Validators.min(0), Validators.max(59)]],
    finish_seconds: [null as number | null, [Validators.min(0), Validators.max(59)]],
    position: [null as number | null],
    registered: [false],
    attended: [false],
    medal: [false],
    event_url: [''],
    certificate_url: [''],
    notes: [''],
  });

  ngOnInit(): void {
    this.runningService.listShoes().subscribe({ next: (s) => this.shoes.set(s) });
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id === 'new' || (!id && url.includes('new'))) {
      return;
    }
    if (id && url.includes('edit')) {
      this.isEdit = true;
      this.raceId = id;
      this.runningService.getRace(id).subscribe({
        next: (r: RaceEvent) => {
          let fh: number | null = null;
          let fm: number | null = null;
          let fs: number | null = null;
          if (r.finish_time_seconds) {
            fh = Math.floor(r.finish_time_seconds / 3600);
            fm = Math.floor((r.finish_time_seconds % 3600) / 60);
            fs = r.finish_time_seconds % 60;
          }
          this.eventPhotos = [];
          this.eventPhotoChecksums = [];
          for (const url of r.photos ?? []) {
            this.addEventPhoto(url);
          }
          const cert = r.certificate_url ?? '';
          if (cert.includes('/files/') && cert.includes('/content')) {
            this.certificateFileUrl = cert;
          }
          this.form.patchValue({
            name: r.name,
            race_date: r.race_date.slice(0, 10),
            distance_type: r.distance_type as any,
            organizer: r.organizer ?? '',
            location: r.location ?? '',
            shoe: r.shoe ?? '',
            bib_number: r.bib_number ?? '',
            finish_hours: fh,
            finish_minutes: fm,
            finish_seconds: fs,
            position: r.position ?? null,
            registered: r.registered,
            attended: r.attended,
            medal: r.medal,
            event_url: r.event_url ?? '',
            certificate_url: cert,
            notes: r.notes ?? '',
          });
        },
      });
    }
  }

  onShoeCreated(name: string): void {
    this.shoes.update((list) => (list.includes(name) ? list : [...list, name].sort()));
    this.runningService.createShoe(name).subscribe({ next: (s) => this.shoes.set(s) });
  }

  onEventImageUploaded(url: string): void {
    if (this.eventPhotos.some((p) => p.url === url)) return;
    this.addEventPhoto(url);
  }

  removeEventPhoto(index: number): void {
    this.eventPhotos = this.eventPhotos.filter((_, i) => i !== index);
    this.refreshEventPhotoChecksums();
  }

  private addEventPhoto(url: string): void {
    const item: EventPhotoItem = { url, preview: url };
    this.eventPhotos = [...this.eventPhotos, item];
    const fileId = url.match(/\/files\/([0-9a-f-]{36})\/content/i)?.[1];
    if (fileId) {
      this.filesService.tokenUrl(fileId).subscribe({
        next: (preview) => {
          this.eventPhotos = this.eventPhotos.map((p) => (p.url === url ? { ...p, preview } : p));
        },
      });
      this.filesService.get(fileId).subscribe({
        next: (record) => {
          if (record.checksum_sha256) {
            this.eventPhotoChecksums = [...this.eventPhotoChecksums, record.checksum_sha256];
          }
        },
      });
    }
  }

  private refreshEventPhotoChecksums(): void {
    const ids = this.eventPhotos
      .map((p) => p.url.match(/\/files\/([0-9a-f-]{36})\/content/i)?.[1])
      .filter((id): id is string => !!id);
    if (!ids.length) {
      this.eventPhotoChecksums = [];
      return;
    }
    const sums: string[] = [];
    let pending = ids.length;
    for (const id of ids) {
      this.filesService.get(id).subscribe({
        next: (record) => {
          if (record.checksum_sha256) sums.push(record.checksum_sha256);
          pending -= 1;
          if (pending === 0) this.eventPhotoChecksums = [...sums];
        },
        error: () => {
          pending -= 1;
          if (pending === 0) this.eventPhotoChecksums = [...sums];
        },
      });
    }
  }

  onCertificateUploaded(url: string): void {
    this.certificateFileUrl = url;
    this.form.patchValue({ certificate_url: url });
  }

  onCertificateUploadCleared(): void {
    this.certificateFileUrl = null;
    if (this.form.controls.certificate_url.value.includes('/files/')) {
      this.form.patchValue({ certificate_url: '' });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    this.error = '';
    const raw = this.form.getRawValue();

    const fh = raw.finish_hours ?? 0;
    const fm = raw.finish_minutes ?? 0;
    const fs = raw.finish_seconds ?? 0;
    const finish_time_seconds =
      raw.attended && (fh || fm || fs) ? fh * 3600 + fm * 60 + fs : null;
    const attended = raw.attended || !!finish_time_seconds;

    const payload = {
      name: raw.name,
      race_date: raw.race_date,
      distance_type: raw.distance_type,
      organizer: raw.organizer || null,
      location: raw.location || null,
      shoe: raw.shoe || null,
      bib_number: raw.bib_number || null,
      finish_time_seconds,
      position: raw.position ?? null,
      registered: raw.registered,
      attended,
      medal: raw.medal,
      event_url: raw.event_url || null,
      certificate_url: raw.certificate_url || null,
      notes: raw.notes || null,
      photos: this.eventPhotos.map((p) => p.url),
    };

    const req =
      this.isEdit && this.raceId
        ? this.runningService.updateRace(this.raceId, payload)
        : this.runningService.createRace(payload);

    req.subscribe({
      next: (race) => {
        if (!race?.id) {
          this.error = 'Event saved but response was invalid. Check the events list.';
          this.saving = false;
          return;
        }
        void this.router.navigate(['/running'], { queryParams: { tab: 'events' } });
      },
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save event';
        this.saving = false;
      },
    });
  }

  isPastRaceDate(): boolean {
    return isPastDate(this.form.controls.race_date.value);
  }
}
