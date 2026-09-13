import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  RaceEvent,
  formatDuration,
  getRaceStatus,
  raceDistanceLabel,
  raceStatusLabel,
} from '../models/running.models';

@Component({
  selector: 'app-running-events-tab',
  standalone: true,
  imports: [RouterLink, DatePipe],
  host: { class: 'contents' },
  template: `
    <div class="space-y-2">
      @if (races.length === 0) {
        <div class="panel">
          <div class="empty-state" style="padding: 2rem 1rem">
            <div class="empty-state__icon">🏅</div>
            <p class="empty-state__title">No race events yet</p>
            <p class="empty-state__desc">Record your races, marathons, and competitions.</p>
            <a routerLink="/running/races/new" class="btn-primary text-xs no-underline mt-2">Add first event</a>
          </div>
        </div>
      } @else {
        @for (race of races; track race.id) {
          <div class="panel" style="display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2 mb-1">
                <a [routerLink]="['/running/races', race.id]" class="link font-semibold text-sm">{{ race.name }}</a>
                <span class="badge badge--default">{{ raceLabel(race) }}</span>
                <span
                  class="badge"
                  [class.badge--success]="raceStatus(race) === 'completed'"
                  [class.badge--warning]="raceStatus(race) === 'registered'"
                  [class.badge--default]="raceStatus(race) === 'upcoming' || raceStatus(race) === 'missed'"
                >{{ raceStatusLabel(raceStatus(race)) }}</span>
                @if (race.medal) { <span class="badge badge--warning">🏅 Medal</span> }
              </div>
              <p class="text-xs" style="color: var(--text-muted)">
                {{ race.race_date | date: 'mediumDate' }}
                @if (race.location) { · {{ race.location }} }
                @if (race.shoe) { · {{ race.shoe }} }
                @if (race.finish_time_seconds) { · Finish: {{ formatDuration(race.finish_time_seconds) }} }
                @if (race.position) { · #{{ race.position }} }
              </p>
              @if (race.event_url || race.certificate_url) {
                <p class="text-xs mt-1 flex flex-wrap gap-2">
                  @if (race.event_url) {
                    <a [href]="race.event_url" target="_blank" rel="noopener noreferrer" class="link">Event page</a>
                  }
                  @if (race.certificate_url) {
                    <a [href]="race.certificate_url" target="_blank" rel="noopener noreferrer" class="link">Certificate</a>
                  }
                </p>
              }
            </div>
            <div class="shrink-0 flex flex-wrap gap-2">
              <a [routerLink]="['/running/races', race.id, 'edit']" class="btn-ghost text-xs no-underline">Edit</a>
              <button type="button" class="btn-ghost text-xs" style="color: var(--danger)" (click)="removeRace.emit(race.id)">Delete</button>
            </div>
          </div>
        }
      }
    </div>
  `,
})
export class RunningEventsTabComponent {
  @Input({ required: true }) races: RaceEvent[] = [];
  @Output() readonly removeRace = new EventEmitter<string>();

  readonly formatDuration = formatDuration;
  readonly raceStatusLabel = raceStatusLabel;

  raceLabel(race: RaceEvent): string {
    return raceDistanceLabel(race.distance_type, race.distance_km);
  }

  raceStatus(race: RaceEvent) {
    return getRaceStatus(race);
  }
}
