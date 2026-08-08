import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LearningConcept, SessionStats } from './models/learning.models';
import { LearningService } from './services/learning.service';

/** Curriculum week 1..24 from track start 2026-08-08. */
function curriculumWeek(d = new Date()): number {
  const start = new Date(2026, 7, 8); // Aug 8 2026
  const diffDays = Math.floor((d.getTime() - start.getTime()) / 86400000);
  if (diffDays < 0) return 1;
  const week = Math.floor(diffDays / 7) + 1;
  return Math.min(24, Math.max(1, week));
}

@Component({
  selector: 'app-learning-today',
  standalone: true,
  imports: [RouterLink, ReactiveFormsModule],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Today — Week {{ week() }}</h1>
        <a routerLink="/learning/tracks" class="input-field !w-auto inline-flex items-center no-underline text-xs">Tracks</a>
      </div>

      @if (stats(); as s) {
        <div class="panel text-sm" style="color: var(--text-muted)">
          {{ s.minutes_this_week }} min this week · streak {{ s.study_streak_days }}d ·
          {{ s.concepts_gated }}/{{ s.concepts_total }} concepts gated
        </div>
      }

      @if (loading()) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (concepts().length === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">
            No concepts for this week. Seed a track first.
          </p>
        </div>
      } @else {
        <ul class="space-y-2">
          @for (c of concepts(); track c.id) {
            <li class="panel space-y-2">
              <div class="flex justify-between gap-2">
                <a [routerLink]="['/learning/concepts', c.id]" class="link font-medium">{{ c.title }}</a>
                <span class="text-xs" style="color: var(--text-muted)">{{ c.confidence }}/5</span>
              </div>
              @if (c.summary) {
                <p class="text-sm" style="color: var(--text-muted)">{{ c.summary }}</p>
              }
              <form class="flex flex-wrap gap-2 items-end text-sm" [formGroup]="sessionForm" (ngSubmit)="logSession(c)">
                <input class="input-field !w-20" type="number" min="1" max="480" formControlName="minutes" placeholder="min" />
                <input class="input-field !w-16" type="number" min="1" max="5" formControlName="confidence" />
                <button type="submit" class="btn-primary text-xs" [disabled]="sessionForm.invalid || savingId() === c.id">
                  Log session
                </button>
              </form>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class LearningTodayComponent implements OnInit {
  private readonly learningService = inject(LearningService);
  private readonly fb = inject(FormBuilder);
  week = signal(curriculumWeek());
  concepts = signal<LearningConcept[]>([]);
  stats = signal<SessionStats | null>(null);
  loading = signal(false);
  savingId = signal<string | null>(null);
  sessionForm = this.fb.nonNullable.group({
    minutes: [45, [Validators.required, Validators.min(1)]],
    confidence: [3, [Validators.required, Validators.min(1), Validators.max(5)]],
  });

  ngOnInit(): void {
    this.loading.set(true);
    this.learningService.listConcepts(undefined, this.week()).subscribe({
      next: (data) => {
        this.concepts.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
    this.learningService.sessionStats().subscribe({
      next: (s) => this.stats.set(s),
    });
  }

  logSession(c: LearningConcept): void {
    if (this.sessionForm.invalid) return;
    const raw = this.sessionForm.getRawValue();
    this.savingId.set(c.id);
    const today = new Date().toISOString().slice(0, 10);
    this.learningService
      .createSession({
        item_id: c.item_id,
        concept_id: c.id,
        session_date: today,
        minutes: raw.minutes,
        confidence: raw.confidence,
      })
      .subscribe({
        next: () => {
          this.savingId.set(null);
          this.learningService.sessionStats().subscribe({ next: (s) => this.stats.set(s) });
          this.learningService.listConcepts(undefined, this.week()).subscribe({
            next: (data) => this.concepts.set(data),
          });
        },
        error: () => this.savingId.set(null),
      });
  }
}
