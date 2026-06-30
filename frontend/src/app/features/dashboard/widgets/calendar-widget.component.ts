import { DatePipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { CalendarPreviewItem } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-calendar-widget',
  standalone: true,
  imports: [DatePipe, WidgetSkeletonComponent],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0">Calendar Preview</div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (events.length === 0) {
        <p class="p-3 text-sm text-gray-600">No upcoming events</p>
      } @else {
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (event of events; track event.id) {
            <li class="flex justify-between gap-2 px-3 py-2">
              <span>{{ event.title }}</span>
              <span class="text-xs text-gray-500">{{ event.starts_at | date: 'MMM d, HH:mm' }}</span>
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
