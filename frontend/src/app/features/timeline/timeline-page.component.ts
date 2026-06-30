import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

interface TimelineItem {
  module: string;
  entity_type: string;
  id: string;
  title: string;
  occurred_at: string;
  route: string;
}

@Component({
  selector: 'app-timeline-page',
  standalone: true,
  imports: [DatePipe, RouterLink],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Life Timeline</h1>
      <p class="text-sm text-gray-600">Chronological view across all modules.</p>
      @if (loading) {
        <p class="text-sm text-gray-600">Loading…</p>
      } @else {
        <ul class="panel !p-0 divide-y divide-[var(--xp-border)] text-sm">
          @for (e of events; track e.id + e.module) {
            <li class="flex items-start justify-between gap-2 px-3 py-2">
              <div>
                <a [routerLink]="e.route" class="text-[var(--xp-blue)] underline">{{ e.title }}</a>
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
  private readonly http = inject(HttpClient);
  events: TimelineItem[] = [];
  loading = false;

  ngOnInit(): void {
    this.loading = true;
    this.http.get<TimelineItem[]>(`${environment.apiUrl}/timeline`).subscribe({
      next: (data) => {
        this.events = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
