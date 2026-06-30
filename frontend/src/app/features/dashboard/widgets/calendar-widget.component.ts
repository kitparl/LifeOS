import { DatePipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CalendarPreviewItem } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-calendar-widget',
  standalone: true,
  imports: [DatePipe, WidgetSkeletonComponent, RouterLink],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0 flex items-center justify-between pr-2">
        <span>Calendar Preview</span>
        <a routerLink="/calendar" class="text-[10px] font-normal underline">All</a>
      </div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (events.length === 0) {
        <p class="p-3 text-sm text-gray-600">
          No upcoming events.
          <a routerLink="/calendar/new" class="text-[var(--xp-blue)] underline">Add one</a>
        </p>
      } @else {
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (event of events; track event.id) {
            <li class="flex justify-between gap-2 px-3 py-2">
              <a [routerLink]="['/calendar', event.id]" class="hover:underline">{{ event.title }}</a>
              <span class="text-xs text-gray-500 shrink-0">{{ event.starts_at | date: 'MMM d, HH:mm' }}</span>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class CalendarWidgetComponent {
  @Input() loading = false;
  @Input() events: CalendarPreviewItem[] = [];
}
