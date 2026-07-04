import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Run, WEATHER_OPTIONS, durationToSeconds, secondsToParts } from './models/running.models';
import { RunningService } from './services/running.service';

@Component({
  selector: 'app-run-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div style="max-width: 520px">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar">{{ isEdit ? 'Edit Run' : 'Log Run' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="form-label" for="run_date">Date</label>
              <input id="run_date" class="input-field mt-1" type="date" formControlName="run_date" />
            </div>
            <div>
              <label class="form-label" for="distance_km">Distance (km)</label>
              <input id="distance_km" class="input-field mt-1" type="number" step="0.01" min="0.1" formControlName="distance_km" />
            </div>
          </div>

          <div>
            <label class="form-label">Duration (h / min / sec)</label>
            <div class="grid grid-cols-3 gap-2 mt-1">
              <div>
                <input class="input-field" type="number" min="0" formControlName="hours" placeholder="0h" />
              </div>
              <div>
                <input class="input-field" type="number" min="0" max="59" formControlName="minutes" placeholder="min" />
              </div>
              <div>
                <input class="input-field" type="number" min="0" max="59" formControlName="seconds" placeholder="sec" />
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="form-label" for="weather">Weather</label>
              <select id="weather" class="input-field mt-1" formControlName="weather">
                <option value="">—</option>
                @for (w of weatherOptions; track w) {
                  <option [value]="w">{{ w }}</option>
                }
              </select>
            </div>
            <div>
              <label class="form-label" for="location">Location</label>
              <input id="location" class="input-field mt-1" formControlName="location" placeholder="City, park, trail…" />
            </div>
          </div>

          <div>
            <label class="form-label" for="notes">Notes</label>
            <textarea id="notes" class="input-field mt-1" style="min-height: 72px; resize: vertical" formControlName="notes" placeholder="How did it feel?"></textarea>
          </div>

          @if (error) {
            <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : 'Save Run' }}
            </button>
            <a routerLink="/running" class="btn-secondary no-underline">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class RunFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly runningService = inject(RunningService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  weatherOptions = WEATHER_OPTIONS;
  isEdit = false;
  runId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    run_date: [new Date().toISOString().slice(0, 10), Validators.required],
    distance_km: [5, [Validators.required, Validators.min(0.1)]],
    hours: [0, [Validators.min(0)]],
    minutes: [25, [Validators.min(0)]],
    seconds: [0, [Validators.min(0), Validators.max(59)]],
    weather: [''],
    location: [''],
    notes: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.runId = id;
      this.runningService.getRun(id).subscribe({
        next: (run: Run) => {
          const parts = secondsToParts(run.duration_seconds);
          this.form.patchValue({
            run_date: run.run_date.slice(0, 10),
            distance_km: run.distance_km,
            hours: parts.hours,
            minutes: parts.minutes,
            seconds: parts.seconds,
            weather: run.weather ?? '',
            location: run.location ?? '',
            notes: run.notes ?? '',
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
    const duration_seconds = durationToSeconds(raw.hours, raw.minutes, raw.seconds);
    if (duration_seconds <= 0) {
      this.error = 'Duration must be greater than zero';
      this.saving = false;
      return;
    }
    const payload = {
      run_date: raw.run_date,
      distance_km: raw.distance_km,
      duration_seconds,
      weather: raw.weather || null,
      location: raw.location || null,
      notes: raw.notes || null,
    };

    const req =
      this.isEdit && this.runId
        ? this.runningService.updateRun(this.runId, payload)
        : this.runningService.createRun(payload);

    req.subscribe({
      next: (run) => this.router.navigate(['/running', run.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save run';
        this.saving = false;
      },
    });
  }
}
