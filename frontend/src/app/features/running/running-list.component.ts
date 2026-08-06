import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  RaceEvent,
  RunListItem,
  RunningStats,
  formatDuration,
  formatPace,
  getRaceStatus,
  raceDistanceLabel,
  raceStatusLabel,
} from './models/running.models';
import { RunningService } from './services/running.service';

@Component({
  selector: 'app-running-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-4">
      <!-- Page header -->
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold" style="color: var(--text)">Running</h1>
        <div class="flex gap-2">
          <a routerLink="/running/races/new" class="btn-secondary text-xs no-underline">Add Event</a>
          <a routerLink="/running/new" class="btn-primary text-xs no-underline">Log Run</a>
        </div>
      </div>

      <!-- Stats row -->
      @if (stats) {
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="panel">
            <p class="text-xs" style="color: var(--text-muted)">This week</p>
            <p class="text-xl font-semibold mt-0.5">{{ stats.weekly_km }} <span class="text-sm font-normal" style="color: var(--text-muted)">/ {{ stats.weekly_goal_km }} km</span></p>
            <div class="progress-bar mt-2">
              <div class="progress-bar__fill" [style.width.%]="Math.min((stats.weekly_km / stats.weekly_goal_km) * 100, 100)"></div>
            </div>
          </div>
          <div class="panel">
            <p class="text-xs" style="color: var(--text-muted)">Events</p>
            <div class="stat-row mt-0.5">
              <div>
                <p class="stat-figure">{{ stats.events_attended }}</p>
                <p class="stat-caption">Attended</p>
              </div>
              <div>
                <p class="stat-figure stat-figure--plain">{{ stats.events_registered }}</p>
                <p class="stat-caption">Registered</p>
              </div>
            </div>
            <div class="stat-divider"></div>
            <p class="stat-caption">Last event</p>
            <p class="stat-event-name">{{ stats.last_event_name || '—' }}</p>
            <p class="stat-caption">
              {{ stats.last_event_date ? (stats.last_event_date | date: 'mediumDate') : '—' }}
            </p>
          </div>
          <div class="panel">
            <p class="text-xs" style="color: var(--text-muted)">Distance in events</p>
            <div class="stat-row mt-0.5">
              <div>
                <p class="stat-figure">{{ stats.event_total_km }} <span class="stat-unit">km</span></p>
                <p class="stat-caption">Lifetime</p>
              </div>
              <div>
                <p class="stat-figure stat-figure--plain">{{ stats.event_year_km }} <span class="stat-unit">km</span></p>
                <p class="stat-caption">In {{ stats.event_year }}</p>
              </div>
            </div>
            <div class="stat-divider"></div>
            <p class="stat-caption">Next event</p>
            <p class="stat-event-name">{{ stats.next_event_name || '—' }}</p>
            <p class="stat-caption">
              {{ stats.next_event_date ? (stats.next_event_date | date: 'mediumDate') : '—' }}
            </p>
          </div>
        </div>
      }

      @if (stats?.shoe_totals?.length) {
        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Distance by shoe</div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr>
                  <th class="px-3 py-2 text-left">Shoe</th>
                  <th class="px-3 py-2 text-left">Km</th>
                  <th class="px-3 py-2 text-left">Runs</th>
                  <th class="px-3 py-2 text-left">Last run</th>
                </tr>
              </thead>
              <tbody>
                @for (s of stats!.shoe_totals; track s.shoe) {
                  <tr style="border-bottom: 1px solid var(--border)">
                    <td class="px-3 py-2">
                      <button type="button" class="link text-sm" (click)="filterByShoe(s.shoe)">{{ s.shoe }}</button>
                    </td>
                    <td class="px-3 py-2">{{ s.total_km }} km</td>
                    <td class="px-3 py-2">{{ s.run_count }}</td>
                    <td class="px-3 py-2 text-xs" style="color: var(--text-muted)">
                      {{ s.last_run_date ? (s.last_run_date | date: 'mediumDate') : '—' }}
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      }

      <!-- Tabs -->
      <div class="flex gap-0" style="border-bottom: 1px solid var(--border)">
        @for (tab of tabs; track tab.id) {
          <button
            type="button"
            class="tab-btn"
            [class.tab-btn--active]="activeTab() === tab.id"
            (click)="activeTab.set(tab.id)"
          >{{ tab.label }}</button>
        }
      </div>

      <!-- ===== Tab: Previous Runs ===== -->
      @if (activeTab() === 'runs') {
        <div class="flex flex-wrap items-center gap-2 text-sm">
          <label class="text-xs" style="color: var(--text-muted)">Filter by shoe</label>
          <select class="input-field !w-auto" [value]="shoeFilter()" (change)="onShoeFilter($event)">
            <option value="">All shoes</option>
            @for (s of shoeOptions; track s) {
              <option [value]="s">{{ s }}</option>
            }
          </select>
          @if (shoeFilter()) {
            <button type="button" class="btn-ghost text-xs" (click)="filterByShoe('')">Clear</button>
          }
        </div>
        <div class="panel !p-0 overflow-hidden">
          @if (loading) {
            <div class="empty-state">
              <div class="skeleton" style="width: 160px; height: 14px"></div>
            </div>
          } @else if (runs.length === 0) {
            <div class="empty-state">
              <div class="empty-state__icon">🏃</div>
              <p class="empty-state__title">No runs yet</p>
              <p class="empty-state__desc">Log your first run to start tracking your progress.</p>
              <a routerLink="/running/new" class="btn-primary text-xs no-underline mt-2">Log first run</a>
            </div>
          } @else {
            <div class="overflow-x-auto">
              <table class="w-full text-sm" style="min-width: 520px">
                <thead>
                  <tr>
                    <th class="px-3 py-2 text-left">Date</th>
                    <th class="px-3 py-2 text-left">Distance</th>
                    <th class="px-3 py-2 text-left">Duration</th>
                    <th class="px-3 py-2 text-left">Pace</th>
                    <th class="px-3 py-2 text-left">Shoes</th>
                    <th class="px-3 py-2 text-left">Location</th>
                    <th class="px-3 py-2 text-left">Weather</th>
                    <th class="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  @for (run of runs; track run.id) {
                    <tr style="border-bottom: 1px solid var(--border)">
                      <td class="px-3 py-2">
                        <a
                          [routerLink]="run.source === 'race' ? ['/running/races', run.id] : ['/running', run.id]"
                          class="link font-medium"
                        >
                          {{ run.run_date | date: 'mediumDate' }}
                        </a>
                        @if (run.source === 'race') {
                          <span class="badge badge--default ml-1">Event</span>
                          @if (run.event_name) {
                            <span class="text-xs ml-1" style="color: var(--text-muted)">{{ run.event_name }}</span>
                          }
                        }
                      </td>
                      <td class="px-3 py-2">{{ run.distance_km }} km</td>
                      <td class="px-3 py-2">
                        {{ run.duration_seconds ? formatDuration(run.duration_seconds) : '—' }}
                      </td>
                      <td class="px-3 py-2">
                        {{ run.pace_min_per_km ? formatPace(run.pace_min_per_km) : '—' }}
                      </td>
                      <td class="px-3 py-2" style="color: var(--text-muted)">{{ run.shoe || '—' }}</td>
                      <td class="px-3 py-2" style="color: var(--text-muted)">{{ run.location || '—' }}</td>
                      <td class="px-3 py-2 capitalize" style="color: var(--text-muted)">{{ run.weather ?? '—' }}</td>
                      <td class="px-3 py-2">
                        <a
                          [routerLink]="run.source === 'race' ? ['/running/races', run.id, 'edit'] : ['/running', run.id, 'edit']"
                          class="link text-xs"
                        >Edit</a>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          }
        </div>
      }

      <!-- ===== Tab: Events & Competitions ===== -->
      @if (activeTab() === 'events') {
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
                      [class.badge--warning]="raceStatus(race) === 'registered' || raceStatus(race) === 'skipped'"
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
                <div class="shrink-0 flex gap-2">
                  <a [routerLink]="['/running/races', race.id, 'edit']" class="btn-ghost text-xs no-underline">Edit</a>
                  <button type="button" class="btn-ghost text-xs" style="color: var(--danger)" (click)="removeRace(race.id)">Delete</button>
                </div>
              </div>
            }
          }
        </div>
      }

      <!-- ===== Tab: Personal Bests ===== -->
      @if (activeTab() === 'bests') {
        <div class="panel !p-0 overflow-hidden">
          @if (stats) {
            <table class="w-full text-sm">
              <thead>
                <tr>
                  <th class="px-3 py-2 text-left">Distance</th>
                  <th class="px-3 py-2 text-left">Pace</th>
                  <th class="px-3 py-2 text-left">Time</th>
                  <th class="px-3 py-2 text-left">Date</th>
                </tr>
              </thead>
              <tbody>
                @for (pb of stats.personal_bests; track pb.distance_type) {
                  <tr style="border-bottom: 1px solid var(--border)">
                    <td class="px-3 py-2 font-medium">{{ pb.label }}</td>
                    <td class="px-3 py-2">{{ pb.pace_min_per_km ? formatPace(pb.pace_min_per_km) : '—' }}</td>
                    <td class="px-3 py-2">{{ pb.duration_seconds ? formatDuration(pb.duration_seconds) : '—' }}</td>
                    <td class="px-3 py-2" style="color: var(--text-muted)">
                      {{ pb.run_date ? (pb.run_date | date: 'mediumDate') : '—' }}
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          }
        </div>
      }

      <!-- ===== Tab: Goals ===== -->
      @if (activeTab() === 'goals') {
        <div class="panel !p-0 overflow-hidden" style="max-width: 400px">
          <div class="title-bar">Running Goals</div>
          <form class="space-y-3 p-4 text-sm" [formGroup]="settingsForm" (ngSubmit)="saveSettings()">
            <div>
              <label class="form-label">Weekly goal (km)</label>
              <input class="input-field mt-1" type="number" step="0.1" formControlName="weekly_goal_km" />
            </div>
            <div>
              <label class="form-label">Target marathon</label>
              <input class="input-field mt-1" formControlName="target_marathon_name" placeholder="Race name" />
            </div>
            <div>
              <label class="form-label">Marathon date</label>
              <input class="input-field mt-1" type="date" formControlName="target_marathon_date" />
            </div>
            <div>
              <label class="form-label">Half marathon date</label>
              <input class="input-field mt-1" type="date" formControlName="target_half_marathon_date" />
            </div>
            <button type="submit" class="btn-primary text-xs w-full" [disabled]="settingsForm.invalid">Save goals</button>
          </form>
        </div>
      }
    </div>

    <style>
      .form-label {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text);
      }
      .stat-row {
        display: flex;
        gap: 1.5rem;
      }
      .stat-figure {
        font-size: 1.25rem;
        font-weight: 600;
        line-height: 1.25;
        color: var(--primary);
        font-variant-numeric: tabular-nums;
      }
      .stat-figure--plain {
        color: var(--text);
      }
      .stat-unit {
        font-size: 0.8125rem;
        font-weight: 400;
        color: var(--text-muted);
      }
      .stat-caption {
        font-size: 0.75rem;
        color: var(--text-muted);
      }
      .stat-divider {
        height: 1px;
        background: var(--border);
        margin: 0.625rem 0;
      }
      .stat-event-name {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .tab-btn {
        padding: 0.5rem 1rem;
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text-muted);
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        cursor: pointer;
        transition: color 120ms ease, border-color 120ms ease;
        margin-bottom: -1px;
      }
      .tab-btn:hover {
        color: var(--text);
      }
      .tab-btn--active {
        color: var(--primary) !important;
        border-bottom-color: var(--primary) !important;
        font-weight: 600;
      }
    </style>
  `,
})
export class RunningListComponent implements OnInit {
  private readonly runningService = inject(RunningService);
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);

  readonly Math = Math;
  readonly formatDuration = formatDuration;
  readonly formatPace = formatPace;
  readonly raceStatusLabel = raceStatusLabel;

  activeTab = signal<'runs' | 'events' | 'bests' | 'goals'>('runs');

  tabs = [
    { id: 'runs', label: 'Previous Runs' },
    { id: 'events', label: 'Events & Competitions' },
    { id: 'bests', label: 'Personal Bests' },
    { id: 'goals', label: 'Goals' },
  ] as const;

  runs: RunListItem[] = [];
  races: RaceEvent[] = [];
  stats: RunningStats | null = null;
  shoeOptions: string[] = [];
  shoeFilter = signal('');
  loading = false;

  settingsForm = this.fb.nonNullable.group({
    weekly_goal_km: [40, [Validators.required, Validators.min(1)]],
    target_marathon_name: [''],
    target_marathon_date: [''],
    target_half_marathon_date: [''],
  });

  ngOnInit(): void {
    const tab = this.route.snapshot.queryParamMap.get('tab');
    if (tab === 'events' || tab === 'runs' || tab === 'bests' || tab === 'goals') {
      this.activeTab.set(tab);
    }
    this.load();
  }

  load(): void {
    this.loading = true;
    const shoe = this.shoeFilter() || undefined;
    this.runningService.listRuns(shoe).subscribe({
      next: (runs) => {
        this.runs = runs;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
    this.runningService.getStats().subscribe({
      next: (s) => {
        this.stats = s;
        this.shoeOptions = (s.shoe_totals || []).map((t) => t.shoe);
      },
    });
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
    this.runningService.listRaces().subscribe({ next: (r) => (this.races = r) });
  }

  filterByShoe(shoe: string): void {
    this.shoeFilter.set(shoe);
    this.activeTab.set('runs');
    this.load();
  }

  onShoeFilter(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.filterByShoe(value);
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

  removeRace(id: string): void {
    if (!confirm('Delete this race event?')) return;
    this.runningService.deleteRace(id).subscribe({ next: () => this.load() });
  }

  raceLabel(race: RaceEvent): string {
    return raceDistanceLabel(race.distance_type, race.distance_km);
  }

  raceStatus(race: RaceEvent) {
    return getRaceStatus(race);
  }
}
