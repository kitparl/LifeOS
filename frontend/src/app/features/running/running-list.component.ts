import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import {
  RACE_DISTANCES,
  RaceEvent,
  RunListItem,
  RunningStats,
  formatDuration,
  formatPace,
} from './models/running.models';
import { RunningService } from './services/running.service';

@Component({
  selector: 'app-running-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Running</h1>
        <a routerLink="/running/new" class="btn-primary text-xs no-underline">Log Run</a>
      </div>

      @if (stats) {
        <div class="grid gap-3 md:grid-cols-3">
          <div class="panel text-sm">
            <p class="text-xs text-gray-600">This week</p>
            <p class="text-lg font-semibold">{{ stats.weekly_km }} / {{ stats.weekly_goal_km }} km</p>
            <div class="mt-1 h-2 bg-gray-200 border border-[var(--xp-border)]">
              <div
                class="h-full bg-[var(--xp-blue)]"
                [style.width.%]="Math.min((stats.weekly_km / stats.weekly_goal_km) * 100, 100)"
              ></div>
            </div>
          </div>
          <div class="panel text-sm">
            <p class="text-xs text-gray-600">Total runs</p>
            <p class="text-lg font-semibold">{{ stats.total_runs }} ({{ stats.total_km }} km)</p>
          </div>
          <div class="panel text-sm">
            <p class="text-xs text-gray-600">Last run</p>
            <p class="text-lg font-semibold">
              {{ stats.last_run_date ? (stats.last_run_date | date: 'mediumDate') : '—' }}
            </p>
          </div>
        </div>
      }

      <div class="grid gap-3 lg:grid-cols-3">
        <div class="panel !p-0 overflow-hidden lg:col-span-2">
          <div class="title-bar rounded-none border-x-0 border-t-0">Practice Log</div>
          @if (loading) {
            <p class="p-3 text-sm text-gray-600">Loading runs…</p>
          } @else if (runs.length === 0) {
            <p class="p-3 text-sm text-gray-600">
              No runs logged.
              <a routerLink="/running/new" class="text-[var(--xp-blue)] underline">Log your first run</a>
            </p>
          } @else {
            <table class="w-full text-sm">
              <thead class="border-b border-[var(--xp-border)] bg-[#e8e8e8] text-left">
                <tr>
                  <th class="px-3 py-2">Date</th>
                  <th class="px-3 py-2">Distance</th>
                  <th class="px-3 py-2">Duration</th>
                  <th class="px-3 py-2">Pace</th>
                  <th class="px-3 py-2">Weather</th>
                  <th class="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                @for (run of runs; track run.id) {
                  <tr class="border-b border-[var(--xp-border)] hover:bg-[#d6e4f7]">
                    <td class="px-3 py-2">
                      <a [routerLink]="['/running', run.id]" class="text-[var(--xp-blue)] underline">
                        {{ run.run_date | date: 'mediumDate' }}
                      </a>
                    </td>
                    <td class="px-3 py-2">{{ run.distance_km }} km</td>
                    <td class="px-3 py-2">{{ formatDuration(run.duration_seconds) }}</td>
                    <td class="px-3 py-2">{{ formatPace(run.pace_min_per_km) }}</td>
                    <td class="px-3 py-2 capitalize">{{ run.weather ?? '—' }}</td>
                    <td class="px-3 py-2">
                      <a [routerLink]="['/running', run.id, 'edit']" class="text-xs underline">Edit</a>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          }
        </div>

        <div class="space-y-3">
          <div class="panel !p-0 overflow-hidden">
            <div class="title-bar rounded-none border-x-0 border-t-0">Personal Bests</div>
            @if (stats) {
              <ul class="divide-y divide-[var(--xp-border)] text-sm">
                @for (pb of stats.personal_bests; track pb.distance_type) {
                  <li class="flex items-center justify-between px-3 py-2">
                    <span>{{ pb.label }}</span>
                    <span class="text-xs text-gray-600">
                      @if (pb.pace_min_per_km) {
                        {{ formatPace(pb.pace_min_per_km) }}
                      } @else {
                        —
                      }
                    </span>
                  </li>
                }
              </ul>
            }
          </div>

          <div class="panel !p-0 overflow-hidden">
            <div class="title-bar rounded-none border-x-0 border-t-0">Goals</div>
            <form class="space-y-2 p-3 text-sm" [formGroup]="settingsForm" (ngSubmit)="saveSettings()">
              <div>
                <label class="mb-1 block text-xs">Weekly goal (km)</label>
                <input class="input-field" type="number" step="0.1" formControlName="weekly_goal_km" />
              </div>
              <div>
                <label class="mb-1 block text-xs">Target marathon</label>
                <input class="input-field" formControlName="target_marathon_name" placeholder="Race name" />
              </div>
              <div>
                <label class="mb-1 block text-xs">Marathon date</label>
                <input class="input-field" type="date" formControlName="target_marathon_date" />
              </div>
              <div>
                <label class="mb-1 block text-xs">Half marathon date</label>
                <input class="input-field" type="date" formControlName="target_half_marathon_date" />
              </div>
              <button type="submit" class="btn-primary text-xs w-full" [disabled]="settingsForm.invalid">Save goals</button>
            </form>
          </div>
        </div>
      </div>

      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">Upcoming Races</div>
        <div class="p-3 space-y-3">
          <form class="flex flex-wrap gap-2 text-sm" [formGroup]="raceForm" (ngSubmit)="addRace()">
            <input class="input-field flex-1 min-w-[120px]" formControlName="name" placeholder="Race name" />
            <input class="input-field !w-auto" type="date" formControlName="race_date" />
            <select class="input-field !w-auto" formControlName="distance_type">
              @for (d of raceDistances; track d.value) {
                <option [value]="d.value">{{ d.label }}</option>
              }
            </select>
            <label class="flex items-center gap-1 text-xs">
              <input type="checkbox" formControlName="registered" />
              Registered
            </label>
            <button type="submit" class="btn-primary text-xs" [disabled]="raceForm.invalid">Add</button>
          </form>
          @if (races.length === 0) {
            <p class="text-sm text-gray-600">No upcoming races.</p>
          } @else {
            <ul class="divide-y divide-[var(--xp-border)] text-sm">
              @for (race of races; track race.id) {
                <li class="flex items-center justify-between gap-2 py-2">
                  <div>
                    <p class="font-medium">{{ race.name }}</p>
                    <p class="text-xs text-gray-600">
                      {{ race.race_date | date: 'mediumDate' }} · {{ raceLabel(race) }}
                      @if (race.registered) {
                        · Registered
                      }
                    </p>
                  </div>
                  <button type="button" class="text-xs text-red-700" (click)="removeRace(race.id)">Remove</button>
                </li>
              }
            </ul>
          }
        </div>
      </div>
    </div>
  `,
})
export class RunningListComponent implements OnInit {
  private readonly runningService = inject(RunningService);
  private readonly fb = inject(FormBuilder);

  readonly Math = Math;
  readonly formatDuration = formatDuration;
  readonly formatPace = formatPace;
  raceDistances = RACE_DISTANCES;

  runs: RunListItem[] = [];
  races: RaceEvent[] = [];
  stats: RunningStats | null = null;
  loading = false;

  settingsForm = this.fb.nonNullable.group({
    weekly_goal_km: [40, [Validators.required, Validators.min(1)]],
    target_marathon_name: [''],
    target_marathon_date: [''],
    target_half_marathon_date: [''],
  });

  raceForm = this.fb.nonNullable.group({
    name: ['', Validators.required],
    race_date: ['', Validators.required],
    distance_type: ['marathon' as const, Validators.required],
    registered: [false],
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.runningService.listRuns().subscribe({
      next: (runs) => {
        this.runs = runs;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
    this.runningService.getStats().subscribe({ next: (s) => (this.stats = s) });
    this.runningService.getSettings().subscribe({
      next: (s) => {
        this.settingsForm.patchValue({
          weekly_goal_km: s.weekly_goal_km,
          target_marathon_name: s.target_marathon_name ?? '',
          target_marathon_date: s.target_marathon_date?.slice(0, 10) ?? '',
          target_half_marathon_date: s.target_half_marathon_date?.slice(0, 10) ?? '',
        });
      },
    });
    this.runningService.listRaces(true).subscribe({ next: (r) => (this.races = r) });
  }

  saveSettings(): void {
    if (this.settingsForm.invalid) return;
    const raw = this.settingsForm.getRawValue();
    this.runningService
      .updateSettings({
        weekly_goal_km: raw.weekly_goal_km,
        target_marathon_name: raw.target_marathon_name || null,
        target_marathon_date: raw.target_marathon_date || null,
        target_half_marathon_date: raw.target_half_marathon_date || null,
      })
      .subscribe({ next: () => this.load() });
  }

  addRace(): void {
    if (this.raceForm.invalid) return;
    const raw = this.raceForm.getRawValue();
    this.runningService
      .createRace({
        name: raw.name,
        race_date: raw.race_date,
        distance_type: raw.distance_type,
        registered: raw.registered,
      })
      .subscribe({
        next: () => {
          this.raceForm.reset({ name: '', race_date: '', distance_type: 'marathon', registered: false });
          this.load();
        },
      });
  }

  removeRace(id: string): void {
    this.runningService.deleteRace(id).subscribe({ next: () => this.load() });
  }

  raceLabel(race: RaceEvent): string {
    return RACE_DISTANCES.find((d) => d.value === race.distance_type)?.label ?? race.distance_type;
  }
}
