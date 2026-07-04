import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { RACE_DISTANCES, RaceEvent, formatDuration } from './models/running.models';
import { RunningService } from './services/running.service';

@Component({
  selector: 'app-race-event-detail',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (race; as r) {
      <div class="space-y-3">
        <!-- Header -->
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold" style="color: var(--text)">{{ r.name }}</h1>
            <p class="text-xs" style="color: var(--text-muted)">
              {{ r.race_date | date: 'fullDate' }} · {{ raceLabel(r) }}
            </p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/running/races', r.id, 'edit']" class="btn-secondary text-xs no-underline">Edit</a>
            <button type="button" class="btn-danger text-xs" (click)="remove()">Delete</button>
          </div>
        </div>

        <!-- Stat chips row -->
        <div class="flex flex-wrap gap-2">
          @if (r.registered) {
            <span class="badge badge--success">Registered</span>
          }
          @if (r.medal) {
            <span class="badge badge--warning">🏅 Medal</span>
          }
          @if (r.finish_time_seconds) {
            <span class="chip">Finish: {{ formatDuration(r.finish_time_seconds) }}</span>
          }
          @if (r.position) {
            <span class="chip">Position: #{{ r.position }}</span>
          }
          @if (r.bib_number) {
            <span class="chip">Bib: {{ r.bib_number }}</span>
          }
        </div>

        <!-- Details grid -->
        <div class="grid gap-3 sm:grid-cols-2">
          @if (r.organizer) {
            <div class="panel">
              <p class="text-xs" style="color: var(--text-muted)">Organizer</p>
              <p class="font-medium text-sm mt-0.5">{{ r.organizer }}</p>
            </div>
          }
          @if (r.location) {
            <div class="panel">
              <p class="text-xs" style="color: var(--text-muted)">Location</p>
              <p class="font-medium text-sm mt-0.5">{{ r.location }}</p>
            </div>
          }
          @if (r.distance_km) {
            <div class="panel">
              <p class="text-xs" style="color: var(--text-muted)">Distance</p>
              <p class="font-medium text-sm mt-0.5">{{ r.distance_km }} km</p>
            </div>
          }
          @if (r.certificate_url) {
            <div class="panel">
              <p class="text-xs" style="color: var(--text-muted)">Certificate</p>
              <a [href]="r.certificate_url" target="_blank" rel="noopener noreferrer" class="link text-sm mt-0.5 block">View certificate</a>
            </div>
          }
        </div>

        @if (r.notes) {
          <div class="panel">
            <p class="text-xs font-semibold mb-1" style="color: var(--text-muted)">Notes</p>
            <p class="text-sm whitespace-pre-wrap" style="color: var(--text)">{{ r.notes }}</p>
          </div>
        }

        <a routerLink="/running" class="link text-sm">← Back to Running</a>
      </div>
    } @else if (loading) {
      <div class="empty-state">
        <span class="skeleton" style="width: 200px; height: 20px; display: block"></span>
      </div>
    } @else {
      <p class="text-sm" style="color: var(--danger)">Race event not found.</p>
    }
  `,
})
export class RaceEventDetailComponent implements OnInit {
  private readonly runningService = inject(RunningService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly formatDuration = formatDuration;

  race: RaceEvent | null = null;
  loading = true;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading = true;
    this.runningService.getRace(id).subscribe({
      next: (r) => {
        this.race = r;
        this.loading = false;
      },
      error: () => {
        this.race = null;
        this.loading = false;
      },
    });
  }

  remove(): void {
    if (!this.race || !confirm('Delete this race event permanently?')) return;
    this.runningService.deleteRace(this.race.id).subscribe({
      next: () => this.router.navigate(['/running']),
    });
  }

  raceLabel(race: RaceEvent): string {
    return RACE_DISTANCES.find((d) => d.value === race.distance_type)?.label ?? race.distance_type;
  }
}
