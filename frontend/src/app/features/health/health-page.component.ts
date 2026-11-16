import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { HealthBodyTabComponent } from './components/health-body-tab.component';
import { HealthDayFormComponent } from './components/health-day-form.component';
import { HealthSleepTabComponent } from './components/health-sleep-tab.component';
import { HealthTodayTabComponent } from './components/health-today-tab.component';
import { HealthTrendsTabComponent } from './components/health-trends-tab.component';
import { MetricInfo } from './models/health.models';
import { HealthService } from './services/health.service';

type HealthTab = 'today' | 'trends' | 'sleep' | 'body';

const TABS: { id: HealthTab; label: string }[] = [
  { id: 'today', label: 'Today' },
  { id: 'trends', label: 'Trends' },
  { id: 'sleep', label: 'Sleep' },
  { id: 'body', label: 'Body' },
];

@Component({
  selector: 'app-health-page',
  standalone: true,
  imports: [
    HealthTodayTabComponent,
    HealthTrendsTabComponent,
    HealthSleepTabComponent,
    HealthBodyTabComponent,
    HealthDayFormComponent,
  ],
  template: `
    <div class="space-y-4">
      <div class="flex flex-wrap items-end justify-between gap-2" style="border-bottom: 1px solid var(--border)">
        <div class="flex gap-0 overflow-x-auto">
          @for (tab of tabs; track tab.id) {
            <button
              type="button"
              class="tab-btn shrink-0"
              [class.tab-btn--active]="active() === tab.id"
              [attr.data-testid]="'health-tab-' + tab.id"
              (click)="setTab(tab.id)"
            >{{ tab.label }}</button>
          }
        </div>
        <div class="flex shrink-0 gap-2 pb-1">
          <button type="button" class="btn-primary text-xs" data-testid="health-log-day-button" (click)="dayFormOpen.set(true)">Log a day</button>
        </div>
      </div>

      @if (catalogueError()) {
        <p class="text-sm" style="color: var(--danger)">{{ catalogueError() }}</p>
      }

      @switch (active()) {
        @case ('today') { <app-health-today-tab [refresh]="refresh()" (logDay)="dayFormOpen.set(true)" /> }
        @case ('trends') { <app-health-trends-tab [catalogue]="catalogue()" [refresh]="refresh()" /> }
        @case ('sleep') { <app-health-sleep-tab [refresh]="refresh()" /> }
        @case ('body') { <app-health-body-tab [refresh]="refresh()" /> }
      }

      <app-health-day-form
        [open]="dayFormOpen()"
        [catalogue]="catalogue()"
        (closed)="dayFormOpen.set(false)"
        (saved)="onSaved()"
      />
    </div>

    <style>
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
export class HealthPageComponent implements OnInit {
  private readonly health = inject(HealthService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly tabs = TABS;
  readonly active = signal<HealthTab>('today');
  readonly catalogue = signal<MetricInfo[]>([]);
  readonly catalogueError = signal('');
  readonly dayFormOpen = signal(false);
  /** Bumped after a day is saved so the visible tab reloads. */
  readonly refresh = signal(0);

  ngOnInit(): void {
    const tab = this.route.snapshot.queryParamMap.get('tab');
    if (TABS.some((t) => t.id === tab)) this.active.set(tab as HealthTab);
    this.health.getCatalogue().subscribe({
      next: (c) => this.catalogue.set(c),
      error: () => this.catalogueError.set('The list of health metrics could not be loaded.'),
    });
  }

  setTab(id: HealthTab): void {
    this.active.set(id);
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  onSaved(): void {
    this.dayFormOpen.set(false);
    this.refresh.update((n) => n + 1);
  }
}
