import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ListPaginatorComponent } from '../../../shared/pagination/list-paginator.component';
import { RunListItem, formatDuration, formatPace } from '../models/running.models';

@Component({
  selector: 'app-running-runs-tab',
  standalone: true,
  imports: [RouterLink, DatePipe, ListPaginatorComponent],
  host: { class: 'contents' },
  template: `
    <div class="flex flex-wrap items-center gap-2 text-sm">
      <label class="text-xs" style="color: var(--text-muted)">Filter by shoe</label>
      <select class="input-field !w-auto" [value]="shoeFilter" (change)="onShoeFilter($event)">
        <option value="">All shoes</option>
        @for (s of shoeOptions; track s) {
          <option [value]="s">{{ s }}</option>
        }
      </select>
      @if (shoeFilter) {
        <button type="button" class="btn-ghost text-xs" (click)="filterByShoe.emit('')">Clear</button>
      }
    </div>
    <div class="panel !p-0 overflow-hidden">
      @if (loading) {
        <div class="empty-state">
          <div class="skeleton" style="width: 160px; height: 14px"></div>
        </div>
      } @else if (runsTotal === 0) {
        <div class="empty-state">
          <div class="empty-state__icon">🏃</div>
          <p class="empty-state__title">No runs yet</p>
          <p class="empty-state__desc">Log your first run to start tracking your progress.</p>
          <a routerLink="/running/new" class="btn-primary text-xs no-underline mt-2">Log first run</a>
        </div>
      } @else {
        <div class="space-y-2 p-3 md:hidden">
          @for (run of runs; track run.id) {
            <article class="rounded border border-[var(--xp-border)] p-3 space-y-2">
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
              <p class="text-xs" style="color: var(--text-muted)">
                {{ run.distance_km }} km
                · {{ run.duration_seconds ? formatDuration(run.duration_seconds) : '—' }}
                · {{ run.pace_min_per_km ? formatPace(run.pace_min_per_km) : '—' }}
                @if (run.shoe) { · {{ run.shoe }} }
              </p>
              <div class="flex flex-wrap gap-2">
                <a
                  [routerLink]="run.source === 'race' ? ['/running/races', run.id, 'edit'] : ['/running', run.id, 'edit']"
                  class="btn-ghost text-xs no-underline"
                >Edit</a>
                @if (run.source !== 'race') {
                  <button type="button" class="btn-ghost text-xs" style="color: var(--danger)" (click)="removeRun.emit(run)">Delete</button>
                }
              </div>
            </article>
          }
          <app-list-paginator
            [total]="runsTotal"
            [pageSize]="pageSize"
            [currentPage]="currentPage"
            (pageChange)="pageChange.emit($event)"
          />
        </div>
        <div class="hidden overflow-x-auto md:block">
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
                    <div class="flex flex-wrap gap-2">
                      <a
                        [routerLink]="run.source === 'race' ? ['/running/races', run.id, 'edit'] : ['/running', run.id, 'edit']"
                        class="link text-xs"
                      >Edit</a>
                      @if (run.source !== 'race') {
                        <button type="button" class="link text-xs" style="color: var(--danger)" (click)="removeRun.emit(run)">Delete</button>
                      }
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
          <app-list-paginator
            [total]="runsTotal"
            [pageSize]="pageSize"
            [currentPage]="currentPage"
            (pageChange)="pageChange.emit($event)"
          />
        </div>
      }
    </div>
  `,
})
export class RunningRunsTabComponent {
  @Input({ required: true }) runs: RunListItem[] = [];
  @Input({ required: true }) runsTotal = 0;
  @Input({ required: true }) loading = false;
  @Input({ required: true }) shoeOptions: string[] = [];
  @Input({ required: true }) shoeFilter = '';
  @Input({ required: true }) currentPage = 1;
  @Input({ required: true }) pageSize = 25;

  @Output() readonly filterByShoe = new EventEmitter<string>();
  @Output() readonly pageChange = new EventEmitter<number>();
  @Output() readonly removeRun = new EventEmitter<RunListItem>();

  readonly formatDuration = formatDuration;
  readonly formatPace = formatPace;

  onShoeFilter(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.filterByShoe.emit(value);
  }
}
