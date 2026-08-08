import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LearningTrack, TrackProgress } from './models/learning.models';
import { LearningService } from './services/learning.service';

@Component({
  selector: 'app-learning-tracks',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Learning Tracks</h1>
        <div class="flex gap-2">
          <a routerLink="/learning/today" class="input-field !w-auto inline-flex items-center no-underline text-xs">Today</a>
          <a routerLink="/learning" class="input-field !w-auto inline-flex items-center no-underline text-xs">Items</a>
          <button type="button" class="btn-primary text-xs" [disabled]="seeding()" (click)="seedAiTrack()">
            {{ seeding() ? 'Seeding…' : 'Seed AI Systems' }}
          </button>
        </div>
      </div>
      @if (error()) {
        <p class="text-sm" style="color: var(--danger, #c01c28)">{{ error() }}</p>
      }
      @if (loading()) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (tracks().length === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">
            No tracks yet. Seed the AI Systems Engineering track to get started.
          </p>
        </div>
      } @else {
        <ul class="space-y-2">
          @for (t of tracks(); track t.id) {
            <li class="panel">
              <a [routerLink]="['/learning/tracks', t.id]" class="link font-medium">{{ t.title }}</a>
              <p class="text-xs mt-1" style="color: var(--text-muted)">
                {{ t.status }} · {{ t.weekly_hours_target }} hrs/week
                @if (t.target_date) {
                  · target {{ t.target_date }}
                }
              </p>
              @if (t.description) {
                <p class="text-sm mt-1">{{ t.description }}</p>
              }
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class LearningTracksComponent implements OnInit {
  private readonly learningService = inject(LearningService);
  tracks = signal<LearningTrack[]>([]);
  loading = signal(false);
  seeding = signal(false);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.learningService.listTracks().subscribe({
      next: (data) => {
        this.tracks.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.error.set('Failed to load tracks');
      },
    });
  }

  seedAiTrack(): void {
    this.seeding.set(true);
    this.error.set(null);
    this.learningService.seedTrack('ai-systems-engineering').subscribe({
      next: () => {
        this.seeding.set(false);
        this.load();
      },
      error: (err) => {
        this.seeding.set(false);
        this.error.set(err?.error?.detail ?? 'Seed failed');
      },
    });
  }
}

@Component({
  selector: 'app-learning-track-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <a routerLink="/learning/tracks" class="link text-sm">← Tracks</a>
        <a routerLink="/learning/today" class="btn-primary text-xs no-underline">Today</a>
      </div>
      @if (loading()) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (track()) {
        <div class="panel">
          <h1 class="text-lg font-semibold">{{ track()!.title }}</h1>
          @if (progress(); as p) {
            <p class="text-sm mt-1" style="color: var(--text-muted)">
              {{ p.percent_complete }}% · {{ p.concepts_gated }}/{{ p.concepts_total }} gated ·
              {{ p.pace_hours_this_week }}h this week (target {{ p.weekly_hours_target }}h) ·
              streak {{ p.study_streak_days }}d
            </p>
          }
        </div>
        @for (phase of track()!.phases ?? []; track phase.id) {
          <details class="panel !p-0 overflow-hidden" [open]="phase.sort_order === 1">
            <summary class="px-3 py-2 cursor-pointer text-sm font-medium flex justify-between gap-2">
              <span>{{ phase.title }}</span>
              <span style="color: var(--text-muted)">{{ phase.progress }}%</span>
            </summary>
            @if (phase.resources?.length) {
              <div class="border-b border-[var(--xp-border)] px-3 py-2">
                <p class="text-xs mb-1" style="color: var(--text-muted)">Phase resources</p>
                <ul class="space-y-1 text-xs">
                  @for (r of phase.resources ?? []; track r.id) {
                    <li>
                      <a [href]="r.url" target="_blank" rel="noopener" class="link">{{ r.title }}</a>
                      <span style="color: var(--text-muted)"> · {{ r.resource_type }}</span>
                    </li>
                  }
                </ul>
              </div>
            }
            <ul class="divide-y divide-[var(--xp-border)] text-sm">
              @for (c of phase.concepts; track c.id) {
                <li class="flex items-center justify-between gap-2 px-3 py-2">
                  <div>
                    <a [routerLink]="['/learning/concepts', c.id]" class="link">{{ c.title }}</a>
                    <p class="text-xs" style="color: var(--text-muted)">
                      @if (c.week_number) {
                        Week {{ c.week_number }} ·
                      }
                      {{ c.estimated_minutes ?? '—' }} min
                    </p>
                  </div>
                  <span
                    class="text-xs px-2 py-0.5 rounded"
                    style="background: var(--primary-soft); color: var(--primary)"
                    >{{ c.confidence }}/5</span
                  >
                </li>
              }
            </ul>
          </details>
        }
      }
    </div>
  `,
})
export class LearningTrackDetailComponent implements OnInit {
  private readonly learningService = inject(LearningService);
  private readonly route = inject(ActivatedRoute);
  track = signal<LearningTrack | null>(null);
  progress = signal<TrackProgress | null>(null);
  loading = signal(false);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) return;
    this.loading.set(true);
    this.learningService.getTrack(id).subscribe({
      next: (t) => {
        this.track.set(t);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
    this.learningService.getTrackProgress(id).subscribe({
      next: (p) => this.progress.set(p),
    });
  }
}
