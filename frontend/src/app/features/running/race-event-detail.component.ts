import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FilesService } from '../files/services/files.service';
import {
  RaceEvent,
  formatDuration,
  getRaceStatus,
  raceDistanceLabel,
  raceStatusLabel,
} from './models/running.models';
import { RunningService } from './services/running.service';

@Component({
  selector: 'app-race-event-detail',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (race; as r) {
      <div class="space-y-3">
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

        @if (eventImageSrcs.length) {
          <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
            @for (src of eventImageSrcs; track src; let i = $index) {
              <div class="panel !p-0 overflow-hidden">
                <img [src]="src" [alt]="'Event photo ' + (i + 1)" class="max-h-64 w-full object-cover" />
              </div>
            }
          </div>
        }

        <div class="flex flex-wrap gap-2">
          <span
            class="badge"
            [class.badge--success]="raceStatus(r) === 'completed'"
            [class.badge--warning]="raceStatus(r) === 'registered'"
            [class.badge--default]="raceStatus(r) === 'upcoming' || raceStatus(r) === 'missed'"
          >
            {{ raceStatusLabel(raceStatus(r)) }}
          </span>
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
          @if (r.shoe) {
            <span class="chip">Shoes: {{ r.shoe }}</span>
          }
        </div>

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
          @if (r.shoe) {
            <div class="panel">
              <p class="text-xs" style="color: var(--text-muted)">Shoes</p>
              <p class="font-medium text-sm mt-0.5">{{ r.shoe }}</p>
            </div>
          }
          @if (r.distance_km) {
            <div class="panel">
              <p class="text-xs" style="color: var(--text-muted)">Distance</p>
              <p class="font-medium text-sm mt-0.5">{{ r.distance_km }} km</p>
            </div>
          }
          @if (r.certificate_url) {
            <div class="panel space-y-2">
              <p class="text-xs" style="color: var(--text-muted)">Certificate</p>
              @if (certificateImageSrc) {
                <img
                  [src]="certificateImageSrc"
                  alt="Certificate"
                  class="max-h-48 rounded border border-[var(--xp-border)]"
                />
              }
              <a
                [href]="certificateOpenHref || r.certificate_url"
                target="_blank"
                rel="noopener noreferrer"
                class="link text-sm block"
              >
                View certificate
              </a>
            </div>
          }
          @if (r.event_url) {
            <div class="panel">
              <p class="text-xs" style="color: var(--text-muted)">Event source</p>
              <a [href]="r.event_url" target="_blank" rel="noopener noreferrer" class="link text-sm mt-0.5 block">
                View event page
              </a>
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
  private readonly filesService = inject(FilesService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly formatDuration = formatDuration;
  readonly raceStatusLabel = raceStatusLabel;

  race: RaceEvent | null = null;
  loading = true;
  eventImageSrcs: string[] = [];
  certificateImageSrc = '';
  certificateOpenHref = '';

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const id = params.get('id');
      if (!id || id === 'new') {
        void this.router.navigate(['/running/races/new']);
        return;
      }
      this.load(id);
    });
  }

  load(id: string): void {
    this.loading = true;
    this.eventImageSrcs = [];
    this.certificateImageSrc = '';
    this.certificateOpenHref = '';
    this.runningService.getRace(id).subscribe({
      next: (r) => {
        this.race = r;
        this.loading = false;
        this.resolveMedia(r);
      },
      error: () => {
        this.race = null;
        this.loading = false;
      },
    });
  }

  private resolveMedia(r: RaceEvent): void {
    for (const photo of r.photos ?? []) {
      this.resolveDisplayUrl(photo, (src) => {
        if (!this.eventImageSrcs.includes(src)) {
          this.eventImageSrcs = [...this.eventImageSrcs, src];
        }
      });
    }
    if (r.certificate_url) {
      const cert = r.certificate_url;
      const fileId = this.extractFileId(cert);
      if (fileId) {
        this.filesService.tokenUrl(fileId).subscribe({
          next: (url) => {
            this.certificateOpenHref = url;
            if (!/\.pdf(\?|$)/i.test(cert)) {
              this.certificateImageSrc = url;
            }
          },
        });
      } else if (/\.(png|jpe?g|gif|webp)(\?|$)/i.test(cert)) {
        this.certificateImageSrc = cert;
        this.certificateOpenHref = cert;
      } else {
        this.certificateOpenHref = cert;
      }
    }
  }

  private resolveDisplayUrl(url: string, apply: (src: string) => void): void {
    const fileId = this.extractFileId(url);
    if (fileId) {
      this.filesService.tokenUrl(fileId).subscribe({ next: apply, error: () => apply(url) });
    } else {
      apply(url);
    }
  }

  private extractFileId(url: string): string | null {
    const match = url.match(/\/files\/([0-9a-f-]{36})\/content/i);
    return match?.[1] ?? null;
  }

  remove(): void {
    if (!this.race || !confirm('Delete this race event permanently?')) return;
    this.runningService.deleteRace(this.race.id).subscribe({
      next: () => this.router.navigate(['/running']),
    });
  }

  raceLabel(race: RaceEvent): string {
    return raceDistanceLabel(race.distance_type, race.distance_km);
  }

  raceStatus(race: RaceEvent) {
    return getRaceStatus(race);
  }
}
