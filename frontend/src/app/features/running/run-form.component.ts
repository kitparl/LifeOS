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
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Run' : 'Log Run' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Date</label>
            <input class="input-field" type="date" formControlName="run_date" />
          </div>
          <div>
            <label class="mb-1 block">Distance (km)</label>
            <input class="input-field" type="number" step="0.01" min="0.1" formControlName="distance_km" />
          </div>
          <div class="grid grid-cols-3 gap-2">
            <div>
              <label class="mb-1 block">Hours</label>
              <input class="input-field" type="number" min="0" formControlName="hours" />
            </div>
            <div>
              <label class="mb-1 block">Minutes</label>
              <input class="input-field" type="number" min="0" max="59" formControlName="minutes" />
            </div>
            <div>
              <label class="mb-1 block">Seconds</label>
              <input class="input-field" type="number" min="0" max="59" formControlName="seconds" />
            </div>
          </div>
          <div>
            <label class="mb-1 block">Weather</label>
            <select class="input-field" formControlName="weather">
              <option value="">—</option>
              @for (w of weatherOptions; track w) {
                <option [value]="w">{{ w }}</option>
              }
            </select>
          </div>
          <div>
            <label class="mb-1 block">Notes</label>
            <textarea class="input-field min-h-[80px]" formControlName="notes"></textarea>
          </div>
          @if (error) {
            <p class="text-xs text-red-700">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <a routerLink="/running" class="input-field !w-auto inline-flex items-center no-underline text-gray-700">Cancel</a>
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
