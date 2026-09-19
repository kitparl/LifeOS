import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TimelineItem, TimelineService } from './services/timeline.service';

@Component({
  selector: 'app-timeline-page',
  standalone: true,
  imports: [DatePipe, RouterLink],
  template: `
    <div class="space-y-3">
      <p class="text-sm" style="color: var(--text-muted)">Chronological view across all modules.</p>
      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else {
        <ul class="panel !p-0 divide-y divide-[var(--xp-border)] text-sm">
          @for (e of events; track e.id + e.module) {
            <li class="flex items-start justify-between gap-2 px-3 py-2">
              <div>
                <a [routerLink]="e.route" class="link">{{ e.title }}</a>
                <p class="text-xs capitalize text-gray-500">{{ e.module }} · {{ e.entity_type }}</p>
              </div>
              <time class="shrink-0 text-xs text-gray-500">{{ e.occurred_at | date: 'medium' }}</time>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class TimelinePageComponent implements OnInit {
  private readonly timeline = inject(TimelineService);
  events: TimelineItem[] = [];
  loading = false;

  ngOnInit(): void {
    this.loading = true;
    this.timeline.list().subscribe({
      next: (data) => {
        this.events = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
