import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { LifeTimelinePageComponent } from '../life-timeline/life-timeline-page.component';
import { TimelinePageComponent } from './timeline-page.component';

type TimelineTab = 'activity' | 'milestones';

@Component({
  selector: 'app-timeline-hub',
  standalone: true,
  imports: [TimelinePageComponent, LifeTimelinePageComponent],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Timeline</h1>

      <div class="flex gap-1 border-b border-[var(--xp-border)] text-sm">
        @for (t of tabs; track t.id) {
          <button
            type="button"
            class="px-3 py-2"
            [class.bg-[var(--xp-blue)]="tab() === t.id"
            [class.text-white]="tab() === t.id"
            (click)="setTab(t.id)"
          >
            {{ t.label }}
          </button>
        }
      </div>

      @if (tab() === 'activity') {
        <app-timeline-page />
      } @else {
        <app-life-timeline-page />
      }
    </div>
  `,
})
export class TimelineHubComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly tab = signal<TimelineTab>('activity');
  readonly tabs = [
    { id: 'activity' as const, label: 'Activity' },
    { id: 'milestones' as const, label: 'Milestones' },
  ];

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      const t = params.get('tab');
      this.tab.set(t === 'milestones' ? 'milestones' : 'activity');
    });
  }

  setTab(id: TimelineTab): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id === 'activity' ? null : id },
      queryParamsHandling: 'merge',
    });
  }
}
