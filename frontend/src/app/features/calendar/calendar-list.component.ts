import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { EVENT_CATEGORIES, EventListItem } from './models/calendar.models';
import { CalendarService } from './services/calendar.service';

@Component({
  selector: 'app-calendar-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Calendar</h1>
        <a routerLink="/calendar/new" class="btn-primary text-xs no-underline">New Event</a>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="load()">
        <select class="input-field !w-auto" formControlName="view">
          <option value="month">This month</option>
          <option value="week">This week</option>
          <option value="all">All upcoming</option>
        </select>
        <button type="submit" class="btn-primary text-xs">Refresh</button>
      </form>

      @if (loading) {
        <p class="text-sm text-gray-600">Loading events…</p>
      } @else if (events.length === 0) {
        <div class="panel">
          <p class="text-sm text-gray-600">No events scheduled.</p>
          <a routerLink="/calendar/new" class="btn-primary mt-2 inline-block text-xs no-underline">Add event</a>
        </div>
      } @else {
        <div class="panel !p-0 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[#e8e8e8] text-left">
              <tr>
                <th class="px-3 py-2">When</th>
                <th class="px-3 py-2">Title</th>
                <th class="px-3 py-2">Category</th>
                <th class="px-3 py-2">Recurrence</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (event of events; track event.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[#d6e4f7]">
                  <td class="px-3 py-2 text-xs">
                    {{ event.starts_at | date: (event.all_day ? 'mediumDate' : 'medium') }}
                  </td>
                  <td class="px-3 py-2">
                    <a [routerLink]="['/calendar', event.id]" class="text-[var(--xp-blue)] underline">{{ event.title }}</a>
                  </td>
                  <td class="px-3 py-2 capitalize">{{ event.category }}</td>
                  <td class="px-3 py-2 capitalize">{{ event.recurrence === 'none' ? '—' : event.recurrence }}</td>
                  <td class="px-3 py-2">
                    <a [routerLink]="['/calendar', event.id, 'edit']" class="text-xs underline">Edit</a>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
})
export class CalendarListComponent implements OnInit {
  private readonly calendarService = inject(CalendarService);
  private readonly fb = inject(FormBuilder);

  categories = EVENT_CATEGORIES;
  events: EventListItem[] = [];
  loading = false;

  filters = this.fb.nonNullable.group({ view: 'month' });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const view = this.filters.getRawValue().view;
    const now = new Date();
    let start: string | undefined;
    let end: string | undefined;

    if (view === 'week') {
      const ws = new Date(now);
      ws.setDate(now.getDate() - now.getDay());
      ws.setHours(0, 0, 0, 0);
      const we = new Date(ws);
      we.setDate(ws.getDate() + 6);
      we.setHours(23, 59, 59, 999);
      start = ws.toISOString();
      end = we.toISOString();
    } else if (view === 'month') {
      const ms = new Date(now.getFullYear(), now.getMonth(), 1);
      const me = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);
      start = ms.toISOString();
      end = me.toISOString();
    }

    this.calendarService.list(start, end).subscribe({
      next: (data) => {
        this.events = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
