import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MOOD_METRICS, MoodStats } from './models/mood.models';
import { MoodService } from './services/mood.service';

@Component({
  selector: 'app-mood-page',
  standalone: true,
  imports: [ReactiveFormsModule, DatePipe],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Mood</h1>

      <div class="grid gap-3 lg:grid-cols-2">
        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Today's Check-in</div>
          <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="save()">
            @for (metric of metrics; track metric.key) {
              <div>
                <label class="mb-1 flex justify-between text-xs">
                  <span>{{ metric.label }}</span>
                  <span class="text-gray-500">{{ form.get(metric.key)?.value }}/5</span>
                </label>
                <input
                  type="range"
                  class="w-full"
                  min="1"
                  max="5"
                  step="1"
                  [formControlName]="metric.key"
                />
              </div>
            }
            <div>
              <label class="mb-1 block text-xs">Notes</label>
              <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
            </div>
            @if (message) {
              <p class="text-xs text-green-700">{{ message }}</p>
            }
            <button type="submit" class="btn-primary text-xs" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : 'Save today' }}
            </button>
          </form>
        </div>

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">7-Day Averages</div>
          @if (stats) {
            <div class="grid grid-cols-2 gap-2 p-3 text-sm">
              <div class="panel !p-2">
                <p class="text-xs text-gray-600">Stress</p>
                <p class="text-lg font-semibold">{{ stats.avg_stress }}</p>
              </div>
              <div class="panel !p-2">
                <p class="text-xs text-gray-600">Confidence</p>
                <p class="text-lg font-semibold">{{ stats.avg_confidence }}</p>
              </div>
              <div class="panel !p-2">
                <p class="text-xs text-gray-600">Motivation</p>
                <p class="text-lg font-semibold">{{ stats.avg_motivation }}</p>
              </div>
              <div class="panel !p-2">
                <p class="text-xs text-gray-600">Happiness</p>
                <p class="text-lg font-semibold">{{ stats.avg_happiness }}</p>
              </div>
            </div>
            @if (stats.recent.length > 0) {
              <ul class="divide-y divide-[var(--xp-border)] text-sm border-t border-[var(--xp-border)]">
                @for (entry of stats.recent; track entry.id) {
                  <li class="flex justify-between px-3 py-2">
                    <span>{{ entry.log_date | date: 'mediumDate' }}</span>
                    <span class="text-xs text-gray-600">
                      S{{ entry.stress }} C{{ entry.confidence }} M{{ entry.motivation }} H{{ entry.happiness }}
                    </span>
                  </li>
                }
              </ul>
            }
          } @else {
            <p class="p-3 text-sm text-gray-600">Log your mood to see trends.</p>
          }
        </div>
      </div>
    </div>
  `,
})
export class MoodPageComponent implements OnInit {
  private readonly moodService = inject(MoodService);
  private readonly fb = inject(FormBuilder);

  metrics = MOOD_METRICS;
  stats: MoodStats | null = null;
  saving = false;
  message = '';

  form = this.fb.nonNullable.group({
    stress: [3, [Validators.required, Validators.min(1), Validators.max(5)]],
    confidence: [3, [Validators.required, Validators.min(1), Validators.max(5)]],
    motivation: [3, [Validators.required, Validators.min(1), Validators.max(5)]],
    happiness: [3, [Validators.required, Validators.min(1), Validators.max(5)]],
    notes: [''],
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.moodService.getToday().subscribe({
      next: (entry) => {
        if (entry) {
          this.form.patchValue({
            stress: entry.stress,
            confidence: entry.confidence,
            motivation: entry.motivation,
            happiness: entry.happiness,
            notes: entry.notes ?? '',
          });
        }
      },
    });
    this.moodService.getStats(7).subscribe({ next: (s) => (this.stats = s) });
  }

  save(): void {
    if (this.form.invalid) return;
    this.saving = true;
    this.message = '';
    const raw = this.form.getRawValue();
    this.moodService
      .upsertToday({
        stress: raw.stress,
        confidence: raw.confidence,
        motivation: raw.motivation,
        happiness: raw.happiness,
        notes: raw.notes || null,
      })
      .subscribe({
        next: () => {
          this.message = 'Saved for today';
          this.saving = false;
          this.load();
        },
        error: () => (this.saving = false),
      });
  }
}
