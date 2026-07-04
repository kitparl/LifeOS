import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { RACE_DISTANCES, RaceEvent } from './models/running.models';
import { RunningService } from './services/running.service';

@Component({
  selector: 'app-race-event-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div style="max-width: 600px">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar">{{ isEdit ? 'Edit Event' : 'Add Race / Competition' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">

          <div class="grid grid-cols-2 gap-3">
            <div class="col-span-2 sm:col-span-1">
              <label class="form-label" for="name">Event Name</label>
              <input id="name" class="input-field mt-1" formControlName="name" placeholder="e.g. TCS World 10K 2026" />
            </div>
            <div>
              <label class="form-label" for="race_date">Date</label>
              <input id="race_date" class="input-field mt-1" type="date" formControlName="race_date" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="form-label" for="distance_type">Distance</label>
              <select id="distance_type" class="input-field mt-1" formControlName="distance_type">
                @for (d of raceDistances; track d.value) {
                  <option [value]="d.value">{{ d.label }}</option>
                }
              </select>
            </div>
            <div>
              <label class="form-label" for="organizer">Organizer</label>
              <input id="organizer" class="input-field mt-1" formControlName="organizer" placeholder="Event organizer" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="form-label" for="location">Location / City</label>
              <input id="location" class="input-field mt-1" formControlName="location" placeholder="Bengaluru, India" />
            </div>
            <div>
              <label class="form-label" for="bib_number">Bib Number</label>
              <input id="bib_number" class="input-field mt-1" formControlName="bib_number" placeholder="e.g. 4521" />
            </div>
          </div>

          <div class="grid grid-cols-3 gap-2">
            <div>
              <label class="form-label">Finish Time (h:m:s)</label>
              <div class="grid grid-cols-3 gap-1 mt-1">
                <input class="input-field" type="number" min="0" formControlName="finish_hours" placeholder="h" />
                <input class="input-field" type="number" min="0" max="59" formControlName="finish_minutes" placeholder="m" />
                <input class="input-field" type="number" min="0" max="59" formControlName="finish_seconds" placeholder="s" />
              </div>
            </div>
            <div>
              <label class="form-label" for="position">Position / Rank</label>
              <input id="position" class="input-field mt-1" type="number" min="1" formControlName="position" placeholder="e.g. 142" />
            </div>
            <div class="flex items-end gap-3 pb-0.5">
              <label class="flex items-center gap-2 cursor-pointer mt-1">
                <input type="checkbox" formControlName="registered" class="w-4 h-4" />
                <span class="form-label" style="margin: 0">Registered</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" formControlName="medal" class="w-4 h-4" />
                <span class="form-label" style="margin: 0">Medal</span>
              </label>
            </div>
          </div>

          <div>
            <label class="form-label" for="certificate_url">Certificate URL</label>
            <input id="certificate_url" class="input-field mt-1" type="url" formControlName="certificate_url" placeholder="https://…" />
          </div>

          <div>
            <label class="form-label" for="notes">Notes</label>
            <textarea id="notes" class="input-field mt-1" style="min-height: 72px; resize: vertical" formControlName="notes" placeholder="Race report, conditions, memories…"></textarea>
          </div>

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
  `,
})
export class RaceEventFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly runningService = inject(RunningService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  raceDistances = RACE_DISTANCES;
  isEdit = false;
  raceId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    name: ['', Validators.required],
    race_date: ['', Validators.required],
    distance_type: ['marathon' as const, Validators.required],
    organizer: [''],
    location: [''],
    bib_number: [''],
    finish_hours: [0, [Validators.min(0)]],
    finish_minutes: [0, [Validators.min(0), Validators.max(59)]],
    finish_seconds: [0, [Validators.min(0), Validators.max(59)]],
    position: [null as number | null],
    registered: [false],
    medal: [false],
    certificate_url: [''],
    notes: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.includes('edit')) {
      this.isEdit = true;
      this.raceId = id;
      this.runningService.getRace(id).subscribe({
        next: (r: RaceEvent) => {
          let fh = 0, fm = 0, fs = 0;
          if (r.finish_time_seconds) {
            fh = Math.floor(r.finish_time_seconds / 3600);
            fm = Math.floor((r.finish_time_seconds % 3600) / 60);
            fs = r.finish_time_seconds % 60;
          }
          this.form.patchValue({
            name: r.name,
            race_date: r.race_date.slice(0, 10),
            distance_type: r.distance_type as any,
            organizer: r.organizer ?? '',
            location: r.location ?? '',
            bib_number: r.bib_number ?? '',
            finish_hours: fh,
            finish_minutes: fm,
            finish_seconds: fs,
            position: r.position ?? null,
            registered: r.registered,
            medal: r.medal,
            certificate_url: r.certificate_url ?? '',
            notes: r.notes ?? '',
          });
        },
      });
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
    const finish_time_seconds = fh * 3600 + fm * 60 + fs || null;

    const payload = {
      name: raw.name,
      race_date: raw.race_date,
      distance_type: raw.distance_type,
      organizer: raw.organizer || null,
      location: raw.location || null,
      bib_number: raw.bib_number || null,
      finish_time_seconds,
      position: raw.position ?? null,
      registered: raw.registered,
      medal: raw.medal,
      certificate_url: raw.certificate_url || null,
      notes: raw.notes || null,
      photos: [],
    };

    const req =
      this.isEdit && this.raceId
        ? this.runningService.updateRace(this.raceId, payload)
        : this.runningService.createRace(payload);

    req.subscribe({
      next: (race) => this.router.navigate(['/running/races', race.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save event';
        this.saving = false;
      },
    });
  }
}
