import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { RunningBestsTabComponent } from './components/running-bests-tab.component';
import { RunningEventsTabComponent } from './components/running-events-tab.component';
import { RunningGoalsTabComponent } from './components/running-goals-tab.component';
import { RunningRunsTabComponent } from './components/running-runs-tab.component';
import { RunningShoesTabComponent } from './components/running-shoes-tab.component';
import { RunningStatsTabComponent } from './components/running-stats-tab.component';
import {
  RaceEvent,
  RunListItem,
  RunningStats,
} from './models/running.models';
import { RunningService } from './services/running.service';

type RunningTab = 'runs' | 'events' | 'bests' | 'goals' | 'shoes' | 'stats';

@Component({
  selector: 'app-running-list',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    DatePipe,
    RunningRunsTabComponent,
    RunningEventsTabComponent,
    RunningBestsTabComponent,
    RunningGoalsTabComponent,
    RunningShoesTabComponent,
    RunningStatsTabComponent,
  ],
  template: `
    <div class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold" style="color: var(--text)">Running</h1>
        <div class="flex gap-2">
          <a routerLink="/running/races/new" class="btn-secondary text-xs no-underline">Add Event</a>
          <a routerLink="/running/new" class="btn-primary text-xs no-underline">Log Run</a>
        </div>
      </div>

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
            <p class="stat-line mt-0.5">
              <span class="stat-figure">{{ stats.events_attended }}</span>
              <span class="stat-caption">attended</span>
              <span class="stat-sep">·</span>
              <span class="stat-figure stat-figure--plain">{{ stats.events_registered }}</span>
              <span class="stat-caption">registered</span>
            </p>
            <p class="stat-detail mt-1.5">
              Last: <span class="stat-event-name">{{ stats.last_event_name || '—' }}</span>
              @if (stats.last_event_date) {
                <span class="stat-sep">·</span>{{ stats.last_event_date | date: 'mediumDate' }}
              }
            </p>
          </div>
          <div class="panel">
            <p class="text-xs" style="color: var(--text-muted)">Distance in events</p>
            <p class="stat-line mt-0.5">
              <span class="stat-figure">{{ stats.event_total_km }}</span>
              <span class="stat-caption">km total</span>
              <span class="stat-sep">·</span>
              <span class="stat-figure stat-figure--plain">{{ stats.event_year_km }}</span>
              <span class="stat-caption">km in {{ stats.event_year }}</span>
            </p>
            <p class="stat-detail mt-1.5">
              Next: <span class="stat-event-name">{{ stats.next_event_name || '—' }}</span>
              @if (stats.next_event_date) {
                <span class="stat-sep">·</span>{{ stats.next_event_date | date: 'mediumDate' }}
              }
            </p>
          </div>
        </div>
      }

      <div class="flex gap-0 overflow-x-auto" style="border-bottom: 1px solid var(--border)">
        @for (tab of tabs; track tab.id) {
          <button
            type="button"
            class="tab-btn shrink-0"
            [class.tab-btn--active]="activeTab() === tab.id"
            (click)="setTab(tab.id)"
          >{{ tab.label }}</button>
        }
      </div>

      @if (activeTab() === 'runs') {
        <app-running-runs-tab
          [runs]="runs"
          [runsTotal]="runsTotal"
          [loading]="loading"
          [shoeOptions]="shoeOptions"
          [shoeFilter]="shoeFilter()"
          [currentPage]="currentPage"
          [pageSize]="pageSize"
          (filterByShoe)="filterByShoe($event)"
          (pageChange)="setPage($event)"
          (removeRun)="removeRun($event)"
        />
      }

      @if (activeTab() === 'events') {
        <app-running-events-tab [races]="races" (removeRace)="removeRace($event)" />
      }

      @if (activeTab() === 'bests') {
        <app-running-bests-tab [stats]="stats" />
      }

      @if (activeTab() === 'goals') {
        <app-running-goals-tab [settingsForm]="settingsForm" (saveSettings)="saveSettings()" />
      }

      @if (activeTab() === 'shoes') {
        <app-running-shoes-tab [stats]="stats" (filterByShoe)="filterByShoe($event)" />
      }

      @if (activeTab() === 'stats') {
        <app-running-stats-tab [stats]="stats" />
      }
    </div>

    <style>
      .stat-line {
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        gap: 0.3rem 0.4rem;
        line-height: 1.3;
      }
      .stat-figure {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--primary);
        font-variant-numeric: tabular-nums;
      }
      .stat-figure--plain {
        color: var(--text);
      }
      .stat-caption {
        font-size: 0.8125rem;
        color: var(--text-muted);
      }
      .stat-sep {
        color: var(--text-faint);
        margin: 0 0.1rem;
      }
      .stat-detail {
        font-size: 0.75rem;
        color: var(--text-muted);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .stat-event-name {
        font-weight: 500;
        color: var(--text);
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
  private readonly router = inject(Router);
  private readonly confirm = inject(ConfirmService);

  readonly Math = Math;

  activeTab = signal<RunningTab>('events');

  tabs = [
    { id: 'runs', label: 'Previous Runs' },
    { id: 'events', label: 'Events & Competitions' },
    { id: 'bests', label: 'Personal Bests' },
    { id: 'goals', label: 'Goals' },
    { id: 'shoes', label: 'Shoes Stats' },
    { id: 'stats', label: 'Running Stats' },
  ] as const;

  runs: RunListItem[] = [];
  runsTotal = 0;
  races: RaceEvent[] = [];
  stats: RunningStats | null = null;
  shoeOptions: string[] = [];
  shoeFilter = signal('');
  loading = false;
  currentPage = 1;
  readonly pageSize = 25;

  settingsForm = this.fb.nonNullable.group({
    weekly_goal_km: [40, [Validators.required, Validators.min(1)]],
    target_marathon_name: [''],
    target_marathon_date: [''],
    target_half_marathon_date: [''],
  });

  ngOnInit(): void {
    const tab = this.route.snapshot.queryParamMap.get('tab');
    if (tab === 'events' || tab === 'runs' || tab === 'bests' || tab === 'goals' || tab === 'shoes' || tab === 'stats') {
      this.activeTab.set(tab);
    }
    this.load();
  }

  setTab(id: RunningTab): void {
    this.activeTab.set(id);
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  load(): void {
    this.loading = true;
    const shoe = this.shoeFilter() || undefined;
    const offset = (this.currentPage - 1) * this.pageSize;
    this.runningService.listRuns({ shoe, limit: this.pageSize, offset }).subscribe({
      next: (result) => {
        this.runs = result.items;
        this.runsTotal = result.total;
        this.clampPage();
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

  setPage(page: number): void {
    this.currentPage = page;
    this.load();
  }

  private clampPage(): void {
    const totalPages = Math.max(1, Math.ceil(this.runsTotal / this.pageSize));
    if (this.currentPage > totalPages) {
      this.currentPage = totalPages;
      this.load();
    }
  }

  filterByShoe(shoe: string): void {
    this.shoeFilter.set(shoe);
    this.currentPage = 1;
    this.setTab('runs');
    this.load();
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

  async removeRace(id: string): Promise<void> {
    const ok = await this.confirm.confirm('Delete this race event?');
    if (!ok) return;
    this.runningService.deleteRace(id).subscribe({ next: () => this.load() });
  }

  async removeRun(run: RunListItem): Promise<void> {
    if (run.source === 'race') return;
    const ok = await this.confirm.confirm('Delete this run permanently?');
    if (!ok) return;
    this.runningService.deleteRun(run.id).subscribe({ next: () => this.load() });
  }
}
