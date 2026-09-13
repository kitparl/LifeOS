import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { TabHubComponent } from '../../shared/tab-hub/tab-hub.component';
import { LifeTimelinePageComponent } from '../life-timeline/life-timeline-page.component';
import { TimelinePageComponent } from './timeline-page.component';

type TimelineTab = 'activity' | 'milestones';

@Component({
  selector: 'app-timeline-hub',
  standalone: true,
  imports: [TabHubComponent, TimelinePageComponent, LifeTimelinePageComponent],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Timeline</h1>

      <app-tab-hub [tabs]="tabs" [activeId]="tab()" (tabChange)="setTab($event)" />

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
  private readonly destroyRef = inject(DestroyRef);

  readonly tab = signal<TimelineTab>('activity');
  readonly tabs = [
    { id: 'activity' as const, label: 'Activity' },
    { id: 'milestones' as const, label: 'Milestones' },
  ];

  ngOnInit(): void {
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const t = params.get('tab');
      this.tab.set(t === 'milestones' ? 'milestones' : 'activity');
    });
  }

  setTab(id: string): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id === 'activity' ? null : id },
      queryParamsHandling: 'merge',
    });
  }
}
