import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { Run, formatDuration, formatPace } from './models/running.models';
import { RunningService } from './services/running.service';

@Component({
  selector: 'app-run-detail',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (run; as r) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold">{{ r.run_date | date: 'fullDate' }}</h1>
            <p class="text-xs text-gray-600">{{ r.distance_km }} km · {{ formatDuration(r.duration_seconds) }}</p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/running', r.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>

        <div class="grid gap-3 md:grid-cols-3">
          <div class="panel text-sm">
            <p class="text-xs text-gray-600">Distance</p>
            <p class="text-xl font-semibold">{{ r.distance_km }} km</p>
          </div>
          <div class="panel text-sm">
            <p class="text-xs text-gray-600">Duration</p>
            <p class="text-xl font-semibold">{{ formatDuration(r.duration_seconds) }}</p>
          </div>
          <div class="panel text-sm">
            <p class="text-xs text-gray-600">Pace</p>
            <p class="text-xl font-semibold">{{ formatPace(r.pace_min_per_km) }}</p>
          </div>
        </div>

        @if (r.weather) {
          <div class="panel text-sm">
            <p class="font-medium mb-1">Weather</p>
            <p class="capitalize text-gray-700">{{ r.weather }}</p>
          </div>
        }

        @if (r.notes) {
          <div class="panel text-sm">
            <p class="font-medium mb-1">Notes</p>
            <p class="whitespace-pre-wrap text-gray-700">{{ r.notes }}</p>
          </div>
        }

        <a routerLink="/running" class="text-sm text-[var(--xp-blue)] underline">Back to running</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading run…</p>
    } @else {
      <p class="text-sm text-red-700">Run not found.</p>
    }
  `,
})
export class RunDetailComponent implements OnInit {
  private readonly runningService = inject(RunningService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly formatDuration = formatDuration;
  readonly formatPace = formatPace;

  run: Run | null = null;
  loading = false;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading = true;
    this.runningService.getRun(id).subscribe({
      next: (r: Run) => {
        this.run = r;
        this.loading = false;
      },
      error: () => {
        this.run = null;
        this.loading = false;
      },
    });
  }

  remove(): void {
    if (!this.run || !confirm('Delete this run permanently?')) return;
    this.runningService.deleteRun(this.run.id).subscribe({
      next: () => this.router.navigate(['/running']),
    });
  }
}
